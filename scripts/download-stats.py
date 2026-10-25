#!/usr/bin/env python3
"""Collect public GitHub release-asset download counters.

GitHub's counters measure asset downloads, not unique people or installations.
They can include repeated downloads, updater traffic, and project verification.
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


API_ORIGIN = "https://api.github.com"
WEB_ORIGIN = "https://github.com"
DEFAULT_REPOSITORY = "remteh-by/remteh-remote-play"
DEFAULT_OUTPUT = Path("build/download-stats.json")
PER_PAGE = 100
MAX_RELEASE_PAGES = 100
MAX_ASSET_PAGES = 100
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
MAX_DOWNLOAD_COUNT = (1 << 63) - 1
REQUEST_TIMEOUT_SECONDS = 30
PLATFORMS = ("android", "macos", "linux", "bundle")
REPOSITORY_PART = re.compile(r"[A-Za-z0-9_.-]{1,100}\Z")
NEXT_LINK = re.compile(r"(?:^|,)\s*<[^>]+>\s*;[^,]*\brel=\"?next\"?", re.I)


class DownloadStatsError(RuntimeError):
    """The remote response cannot produce a complete trustworthy snapshot."""


class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    """Keep authenticated requests on the one permitted API origin."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        raise DownloadStatsError("GitHub API redirect refused")


def _fixed_host_open(request: urllib.request.Request, *, timeout: int):
    return urllib.request.build_opener(_RejectRedirects()).open(request, timeout=timeout)


def parse_repository(value: str) -> tuple[str, str]:
    parts = value.split("/")
    if len(parts) != 2 or not all(REPOSITORY_PART.fullmatch(part) for part in parts):
        raise DownloadStatsError("repository must be an owner/name pair")
    if any(part in {".", ".."} for part in parts):
        raise DownloadStatsError("repository contains an invalid path component")
    return parts[0], parts[1]


def _require_int(value: Any, field: str, *, positive: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise DownloadStatsError(f"{field} must be an integer")
    minimum = 1 if positive else 0
    if value < minimum or value > MAX_DOWNLOAD_COUNT:
        relation = "positive" if positive else "non-negative"
        raise DownloadStatsError(f"{field} must be a bounded {relation} integer")
    return value


def _require_bool(value: Any, field: str) -> bool:
    if type(value) is not bool:
        raise DownloadStatsError(f"{field} must be a boolean")
    return value


def _require_text(value: Any, field: str, *, limit: int = 512) -> str:
    if not isinstance(value, str) or not value or len(value) > limit:
        raise DownloadStatsError(f"{field} must be a non-empty bounded string")
    if any(ord(character) < 0x20 for character in value):
        raise DownloadStatsError(f"{field} contains control characters")
    return value


def _utc_iso(value: str, field: str) -> str:
    raw = _require_text(value, field, limit=64)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DownloadStatsError(f"{field} must be an ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise DownloadStatsError(f"{field} must include a timezone")
    parsed = parsed.astimezone(timezone.utc)
    return parsed.isoformat(timespec="seconds").replace("+00:00", "Z")


def classify_asset(name: str) -> str:
    """Map a release filename to the public statistics categories."""
    lower = name.casefold()
    if lower.endswith(".apk"):
        return "android"
    # Public complete kits currently use Deckivo-X.Y.Z-kit.zip; older naming
    # may include "bundle", but that word is not required.
    if lower.endswith("-kit.zip"):
        return "bundle"
    if lower.endswith("-sources.zip"):
        return "source"
    if lower.endswith(".dmg") or (
        lower.endswith(".zip")
        and (
            "macos" in lower
            or lower.startswith("mac")
            or re.search(r"(?:^|[-_.])mac(?:[-_.]|$)", lower)
        )
    ):
        return "macos"
    # Linux bNN-source.zip is a runtime update. Its singular suffix deliberately
    # does not match the complete corresponding-source ``-sources.zip`` above.
    if lower.endswith(".zip") and re.search(r"(?:^|[-_.])linux(?:[-_.]|$)", lower):
        return "linux"
    metadata_suffixes = (
        ".json", ".txt", ".sha256", ".sha256sum", ".sha256sums",
        ".sig", ".asc", ".spdx", ".cdx", ".sbom",
    )
    if lower.endswith(metadata_suffixes) or "checksum" in lower:
        return "metadata"
    return "other"


class GitHubClient:
    def __init__(
        self,
        token: str | None = None,
        opener: Callable[..., Any] | None = None,
    ) -> None:
        if token and (
            len(token) > 1024
            or any(ord(character) < 0x20 for character in token)
        ):
            raise DownloadStatsError("GITHUB_TOKEN is not a valid HTTP header value")
        self._token = token or None
        self._opener = opener or _fixed_host_open

    def _request_page(self, path: str, page: int) -> tuple[list[Any], bool]:
        if not path.startswith("/") or "?" in path or "#" in path:
            raise DownloadStatsError("invalid internal API path")
        query = urllib.parse.urlencode({"per_page": PER_PAGE, "page": page})
        url = f"{API_ORIGIN}{path}?{query}"
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Deckivo-download-statistics/1",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        request = urllib.request.Request(url, headers=headers, method="GET")
        try:
            response = self._opener(request, timeout=REQUEST_TIMEOUT_SECONDS)
            try:
                status = getattr(response, "status", None)
                if status is None:
                    status = response.getcode()
                if status != 200:
                    raise DownloadStatsError(f"GitHub API returned HTTP {status}")
                final_url = getattr(response, "geturl", lambda: url)()
                parsed_url = urllib.parse.urlsplit(final_url)
                if parsed_url.scheme != "https" or parsed_url.netloc != "api.github.com":
                    raise DownloadStatsError("GitHub API response came from an unexpected origin")
                raw = response.read(MAX_RESPONSE_BYTES + 1)
                if len(raw) > MAX_RESPONSE_BYTES:
                    raise DownloadStatsError("GitHub API response exceeded the size limit")
                link = response.headers.get("Link", "")
            finally:
                response.close()
        except DownloadStatsError:
            raise
        except (OSError, urllib.error.URLError, http.client.HTTPException) as exc:
            raise DownloadStatsError("GitHub API request failed") from exc

        try:
            payload = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DownloadStatsError("GitHub API returned invalid JSON") from exc
        if not isinstance(payload, list):
            raise DownloadStatsError("GitHub API page must be a JSON array")
        if len(payload) > PER_PAGE:
            raise DownloadStatsError("GitHub API page exceeded the requested item limit")
        return payload, bool(NEXT_LINK.search(link))

    def paginated(self, path: str, *, max_pages: int) -> list[Any]:
        all_items: list[Any] = []
        for page in range(1, max_pages + 1):
            items, link_has_next = self._request_page(path, page)
            all_items.extend(items)
            has_next = link_has_next or len(items) == PER_PAGE
            if not has_next:
                return all_items
            if not items:
                raise DownloadStatsError("GitHub API pagination was inconsistent")
        raise DownloadStatsError("GitHub API pagination exceeded the safety limit")


def _empty_platforms() -> dict[str, int]:
    return {platform: 0 for platform in PLATFORMS}


def _checked_add(total: int, amount: int, field: str) -> int:
    result = total + amount
    if result > MAX_DOWNLOAD_COUNT:
        raise DownloadStatsError(f"{field} exceeded the supported range")
    return result


def collect_statistics(
    repository: str = DEFAULT_REPOSITORY,
    *,
    token: str | None = None,
    opener: Callable[..., Any] | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    owner, name = parse_repository(repository)
    client = GitHubClient(token=token, opener=opener)
    repo_path = "/repos/{}/{}".format(
        urllib.parse.quote(owner, safe=""), urllib.parse.quote(name, safe="")
    )
    release_payloads = client.paginated(
        f"{repo_path}/releases", max_pages=MAX_RELEASE_PAGES
    )

    releases: list[dict[str, Any]] = []
    seen_releases: dict[int, tuple[Any, ...]] = {}
    seen_assets: dict[int, tuple[str, int]] = {}
    total_platforms = _empty_platforms()
    package_total = 0
    total_downloads = 0

    for index, raw_release in enumerate(release_payloads):
        if not isinstance(raw_release, dict):
            raise DownloadStatsError(f"release[{index}] must be an object")
        release_id = _require_int(raw_release.get("id"), f"release[{index}].id", positive=True)
        draft = _require_bool(raw_release.get("draft"), f"release[{index}].draft")
        previous_release = seen_releases.get(release_id)
        if draft:
            identity = (True,)
            if previous_release is not None and previous_release != identity:
                raise DownloadStatsError("conflicting duplicate release id")
            seen_releases[release_id] = identity
            continue
        prerelease = _require_bool(
            raw_release.get("prerelease"), f"release[{index}].prerelease"
        )
        tag = _require_text(raw_release.get("tag_name"), f"release[{index}].tag_name")
        published_at = _utc_iso(
            raw_release.get("published_at"), f"release[{index}].published_at"
        )
        identity = (False, prerelease, tag, published_at)
        if previous_release is not None:
            if previous_release != identity:
                raise DownloadStatsError("conflicting duplicate release id")
            continue
        seen_releases[release_id] = identity

        asset_payloads = client.paginated(
            f"{repo_path}/releases/{release_id}/assets", max_pages=MAX_ASSET_PAGES
        )
        assets: list[dict[str, Any]] = []
        release_platforms = _empty_platforms()
        release_total = 0

        for asset_index, raw_asset in enumerate(asset_payloads):
            prefix = f"release[{index}].assets[{asset_index}]"
            if not isinstance(raw_asset, dict):
                raise DownloadStatsError(f"{prefix} must be an object")
            asset_id = _require_int(raw_asset.get("id"), f"{prefix}.id", positive=True)
            asset_name = _require_text(raw_asset.get("name"), f"{prefix}.name")
            count = _require_int(raw_asset.get("download_count"), f"{prefix}.download_count")
            identity = (asset_name, count)
            previous_asset = seen_assets.get(asset_id)
            if previous_asset is not None:
                if previous_asset != identity:
                    raise DownloadStatsError("conflicting duplicate asset id")
                continue
            seen_assets[asset_id] = identity

            category = classify_asset(asset_name)
            release_total = _checked_add(release_total, count, "release total_downloads")
            if category in release_platforms:
                release_platforms[category] = _checked_add(
                    release_platforms[category], count, f"release platforms.{category}"
                )
            assets.append({"name": asset_name, "count": count, "category": category})

        release_package_total = sum(release_platforms.values())
        if release_package_total > MAX_DOWNLOAD_COUNT:
            raise DownloadStatsError("release package_total exceeded the supported range")
        for platform in PLATFORMS:
            total_platforms[platform] = _checked_add(
                total_platforms[platform], release_platforms[platform], f"platforms.{platform}"
            )
        package_total = _checked_add(package_total, release_package_total, "package_total")
        total_downloads = _checked_add(total_downloads, release_total, "total_downloads")
        release_url = (
            f"{WEB_ORIGIN}/{owner}/{name}/releases/tag/"
            f"{urllib.parse.quote(tag, safe='')}"
        )
        releases.append({
            "tag": tag,
            "url": release_url,
            "published_at": published_at,
            "prerelease": prerelease,
            "package_total": release_package_total,
            "total_downloads": release_total,
            "platforms": release_platforms,
            "assets": assets,
        })

    timestamp = generated_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        raise DownloadStatsError("generated_at must include a timezone")
    generated_at_text = timestamp.astimezone(timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")
    return {
        "schema": 1,
        "repository": repository,
        "generated_at": generated_at_text,
        "package_total": package_total,
        "total_downloads": total_downloads,
        "platforms": total_platforms,
        "releases": releases,
    }


def write_atomic(output: Path, payload: dict[str, Any]) -> None:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, output)
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def generate(
    output: Path = DEFAULT_OUTPUT,
    repository: str = DEFAULT_REPOSITORY,
    *,
    token: str | None = None,
    opener: Callable[..., Any] | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    payload = collect_statistics(
        repository, token=token, opener=opener, generated_at=generated_at
    )
    write_atomic(output, payload)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Collect GitHub release asset download counters"
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY)
    args = parser.parse_args(argv)
    try:
        generate(
            output=args.output,
            repository=args.repository,
            token=os.environ.get("GITHUB_TOKEN"),
        )
    except (DownloadStatsError, OSError) as exc:
        print(f"download statistics failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
