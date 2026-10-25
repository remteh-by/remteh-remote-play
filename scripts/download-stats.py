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
DEFAULT_HISTORY = Path("website/download-history.json")
PER_PAGE = 100
MAX_RELEASE_PAGES = 100
MAX_ASSET_PAGES = 100
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
MAX_DOWNLOAD_COUNT = (1 << 63) - 1
MAX_ASSET_BYTES = 1 << 50
REQUEST_TIMEOUT_SECONDS = 30
PLATFORMS = ("android", "macos", "linux", "bundle")
ASSET_CATEGORIES = frozenset((*PLATFORMS, "source", "metadata", "other"))
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


def _require_int(
    value: Any,
    field: str,
    *,
    positive: bool = False,
    maximum: int = MAX_DOWNLOAD_COUNT,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise DownloadStatsError(f"{field} must be an integer")
    minimum = 1 if positive else 0
    if value < minimum or value > maximum:
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


def _timestamp_text(value: datetime, field: str) -> str:
    if value.tzinfo is None:
        raise DownloadStatsError(f"{field} must include a timezone")
    return value.astimezone(timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")


def _release_url(owner: str, name: str, tag: str) -> str:
    return (
        f"{WEB_ORIGIN}/{owner}/{name}/releases/tag/"
        f"{urllib.parse.quote(tag, safe='')}"
    )


def _releases_url(owner: str, name: str) -> str:
    return f"{WEB_ORIGIN}/{owner}/{name}/releases"


def _require_exact_keys(value: dict[str, Any], expected: set[str], field: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise DownloadStatsError(
            f"{field} has invalid keys (missing={missing}, extra={extra})"
        )


def validate_history(
    payload: Any,
    repository: str = DEFAULT_REPOSITORY,
) -> dict[str, Any]:
    """Validate and normalize the immutable download counter archive."""
    owner, name = parse_repository(repository)
    if not isinstance(payload, dict):
        raise DownloadStatsError("download history root must be an object")
    _require_exact_keys(
        payload, {"schema", "repository", "snapshot_at", "releases"}, "history"
    )
    if type(payload.get("schema")) is not int or payload["schema"] != 1:
        raise DownloadStatsError("download history schema must be integer 1")
    history_repository = _require_text(
        payload.get("repository"), "history.repository", limit=201
    )
    parse_repository(history_repository)
    if history_repository != repository:
        raise DownloadStatsError("download history repository does not match request")
    snapshot_at = _utc_iso(payload.get("snapshot_at"), "history.snapshot_at")
    raw_releases = payload.get("releases")
    if not isinstance(raw_releases, list):
        raise DownloadStatsError("history.releases must be an array")

    releases: list[dict[str, Any]] = []
    seen_release_ids: set[int] = set()
    seen_tags: set[str] = set()
    seen_asset_ids: set[int] = set()
    for release_index, raw_release in enumerate(raw_releases):
        label = f"history.releases[{release_index}]"
        if not isinstance(raw_release, dict):
            raise DownloadStatsError(f"{label} must be an object")
        _require_exact_keys(
            raw_release,
            {
                "release_id", "tag", "url", "published_at", "prerelease",
                "captured_at", "assets",
            },
            label,
        )
        release_id = _require_int(
            raw_release.get("release_id"), f"{label}.release_id", positive=True
        )
        if release_id in seen_release_ids:
            raise DownloadStatsError("duplicate release id in download history")
        seen_release_ids.add(release_id)
        tag = _require_text(raw_release.get("tag"), f"{label}.tag")
        if tag in seen_tags:
            raise DownloadStatsError("duplicate release tag in download history")
        seen_tags.add(tag)
        url = _require_text(raw_release.get("url"), f"{label}.url", limit=2048)
        if url != _release_url(owner, name, tag):
            raise DownloadStatsError(f"{label}.url is not the canonical repository URL")
        published_at = _utc_iso(
            raw_release.get("published_at"), f"{label}.published_at"
        )
        prerelease = _require_bool(
            raw_release.get("prerelease"), f"{label}.prerelease"
        )
        captured_at = _utc_iso(
            raw_release.get("captured_at"), f"{label}.captured_at"
        )
        raw_assets = raw_release.get("assets")
        if not isinstance(raw_assets, list):
            raise DownloadStatsError(f"{label}.assets must be an array")
        assets: list[dict[str, Any]] = []
        seen_names: set[str] = set()
        for asset_index, raw_asset in enumerate(raw_assets):
            asset_label = f"{label}.assets[{asset_index}]"
            if not isinstance(raw_asset, dict):
                raise DownloadStatsError(f"{asset_label} must be an object")
            _require_exact_keys(
                raw_asset,
                {
                    "asset_id", "name", "size_bytes", "download_count",
                    "category", "captured_at",
                },
                asset_label,
            )
            asset_id = _require_int(
                raw_asset.get("asset_id"), f"{asset_label}.asset_id", positive=True
            )
            if asset_id in seen_asset_ids:
                raise DownloadStatsError("duplicate asset id in download history")
            seen_asset_ids.add(asset_id)
            asset_name = _require_text(raw_asset.get("name"), f"{asset_label}.name")
            if asset_name in seen_names:
                raise DownloadStatsError(f"duplicate asset name in {label}")
            seen_names.add(asset_name)
            size_bytes = _require_int(
                raw_asset.get("size_bytes"),
                f"{asset_label}.size_bytes",
                maximum=MAX_ASSET_BYTES,
            )
            download_count = _require_int(
                raw_asset.get("download_count"), f"{asset_label}.download_count"
            )
            category = _require_text(
                raw_asset.get("category"), f"{asset_label}.category", limit=32
            )
            if category not in ASSET_CATEGORIES or category != classify_asset(asset_name):
                raise DownloadStatsError(f"{asset_label}.category is invalid")
            asset_captured_at = _utc_iso(
                raw_asset.get("captured_at"), f"{asset_label}.captured_at"
            )
            assets.append({
                "asset_id": asset_id,
                "name": asset_name,
                "size_bytes": size_bytes,
                "download_count": download_count,
                "category": category,
                "captured_at": asset_captured_at,
            })
        releases.append({
            "release_id": release_id,
            "tag": tag,
            "url": url,
            "published_at": published_at,
            "prerelease": prerelease,
            "captured_at": captured_at,
            "assets": assets,
        })
    return {
        "schema": 1,
        "repository": repository,
        "snapshot_at": snapshot_at,
        "releases": releases,
    }


def load_history(path: Path, repository: str = DEFAULT_REPOSITORY) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DownloadStatsError(f"download history could not be read: {exc}") from exc
    return validate_history(payload, repository)


def collect_live_releases(
    repository: str = DEFAULT_REPOSITORY,
    *,
    token: str | None = None,
    opener: Callable[..., Any] | None = None,
) -> list[dict[str, Any]]:
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
    seen_tags: set[str] = set()
    seen_assets: dict[int, tuple[int, str, int, int]] = {}

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
        if tag in seen_tags:
            raise DownloadStatsError("conflicting duplicate release tag")
        seen_tags.add(tag)
        seen_releases[release_id] = identity

        asset_payloads = client.paginated(
            f"{repo_path}/releases/{release_id}/assets", max_pages=MAX_ASSET_PAGES
        )
        assets: list[dict[str, Any]] = []

        for asset_index, raw_asset in enumerate(asset_payloads):
            prefix = f"release[{index}].assets[{asset_index}]"
            if not isinstance(raw_asset, dict):
                raise DownloadStatsError(f"{prefix} must be an object")
            asset_id = _require_int(raw_asset.get("id"), f"{prefix}.id", positive=True)
            asset_name = _require_text(raw_asset.get("name"), f"{prefix}.name")
            count = _require_int(raw_asset.get("download_count"), f"{prefix}.download_count")
            size_bytes = _require_int(
                raw_asset.get("size"), f"{prefix}.size", maximum=MAX_ASSET_BYTES
            )
            identity = (release_id, asset_name, count, size_bytes)
            previous_asset = seen_assets.get(asset_id)
            if previous_asset is not None:
                if previous_asset != identity:
                    raise DownloadStatsError("conflicting duplicate asset id")
                continue
            seen_assets[asset_id] = identity

            category = classify_asset(asset_name)
            assets.append({
                "asset_id": asset_id,
                "name": asset_name,
                "size_bytes": size_bytes,
                "download_count": count,
                "category": category,
            })

        releases.append({
            "release_id": release_id,
            "tag": tag,
            "url": _release_url(owner, name, tag),
            "published_at": published_at,
            "prerelease": prerelease,
            "assets": assets,
        })
    return releases


def _release_identity(release: dict[str, Any]) -> tuple[Any, ...]:
    return (
        release["release_id"], release["tag"], release["url"],
        release["published_at"], release["prerelease"],
    )


def _assert_release_matches_history(
    live: dict[str, Any], archived: dict[str, Any]
) -> None:
    if _release_identity(live) != _release_identity(archived):
        raise DownloadStatsError("live release conflicts with download history")


def _assert_asset_matches_history(
    live: dict[str, Any], archived: dict[str, Any]
) -> None:
    if (
        live["name"] != archived["name"]
        or live["size_bytes"] != archived["size_bytes"]
        or live["category"] != archived["category"]
    ):
        raise DownloadStatsError("live asset conflicts with download history")
    if live["download_count"] < archived["download_count"]:
        raise DownloadStatsError("live asset download count decreased below history")


def refresh_history_snapshot(
    live_releases: list[dict[str, Any]],
    repository: str = DEFAULT_REPOSITORY,
    *,
    existing: dict[str, Any] | None = None,
    captured_at: datetime | None = None,
) -> dict[str, Any]:
    """Refresh live counters while retaining assets already removed from GitHub."""
    timestamp = _timestamp_text(
        captured_at or datetime.now(timezone.utc), "history snapshot time"
    )
    history = validate_history(existing, repository) if existing is not None else {
        "schema": 1, "repository": repository, "snapshot_at": timestamp, "releases": []
    }
    old_by_id = {release["release_id"]: release for release in history["releases"]}
    old_by_tag = {release["tag"]: release for release in history["releases"]}
    old_assets: dict[int, tuple[int, dict[str, Any]]] = {}
    for release in history["releases"]:
        for asset in release["assets"]:
            old_assets[asset["asset_id"]] = (release["release_id"], asset)

    live_ids = {release["release_id"] for release in live_releases}
    live_tags: set[str] = set()
    refreshed: list[dict[str, Any]] = []
    for live in live_releases:
        if live["tag"] in live_tags:
            raise DownloadStatsError("duplicate live release tag")
        live_tags.add(live["tag"])
        old = old_by_id.get(live["release_id"])
        if old is None and live["tag"] in old_by_tag:
            raise DownloadStatsError("live release tag was recreated with another id")
        if old is not None:
            _assert_release_matches_history(live, old)
        live_asset_ids: set[int] = set()
        assets: list[dict[str, Any]] = []
        for asset in live["assets"]:
            live_asset_ids.add(asset["asset_id"])
            previous = old_assets.get(asset["asset_id"])
            if previous is not None:
                previous_release_id, previous_asset = previous
                if previous_release_id != live["release_id"]:
                    raise DownloadStatsError("live asset moved to another release")
                _assert_asset_matches_history(asset, previous_asset)
            assets.append({**asset, "captured_at": timestamp})
        if old is not None:
            assets.extend(
                asset for asset in old["assets"]
                if asset["asset_id"] not in live_asset_ids
            )
        refreshed.append({
            **{key: live[key] for key in (
                "release_id", "tag", "url", "published_at", "prerelease"
            )},
            "captured_at": timestamp,
            "assets": assets,
        })
    refreshed.extend(
        release for release in history["releases"]
        if release["release_id"] not in live_ids
    )
    refreshed.sort(key=lambda release: release["published_at"], reverse=True)
    return validate_history({
        "schema": 1,
        "repository": repository,
        "snapshot_at": timestamp,
        "releases": refreshed,
    }, repository)


def _merge_live_and_history(
    live_releases: list[dict[str, Any]],
    repository: str,
    history: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], str | None]:
    owner, name = parse_repository(repository)
    combined: list[dict[str, Any]] = []
    live_by_id: dict[int, dict[str, Any]] = {}
    live_by_tag: dict[str, dict[str, Any]] = {}
    live_assets: dict[int, tuple[int, dict[str, Any]]] = {}
    for release in live_releases:
        copied = {
            **release,
            "archived": False,
            "assets": [{**asset, "archived": False} for asset in release["assets"]],
        }
        combined.append(copied)
        live_by_id[release["release_id"]] = copied
        live_by_tag[release["tag"]] = copied
        for asset in copied["assets"]:
            live_assets[asset["asset_id"]] = (release["release_id"], asset)

    if history is None:
        return combined, None
    archive = validate_history(history, repository)
    archived_releases: list[dict[str, Any]] = []
    for archived in archive["releases"]:
        live_release = live_by_id.get(archived["release_id"])
        if live_release is None and archived["tag"] in live_by_tag:
            raise DownloadStatsError("download history tag conflicts with a live release")
        if live_release is not None:
            _assert_release_matches_history(live_release, archived)
        missing_assets: list[dict[str, Any]] = []
        for asset in archived["assets"]:
            current = live_assets.get(asset["asset_id"])
            if current is not None:
                current_release_id, current_asset = current
                if current_release_id != archived["release_id"]:
                    raise DownloadStatsError(
                        "download history asset belongs to another release"
                    )
                _assert_asset_matches_history(current_asset, asset)
                continue
            missing_assets.append({
                **asset,
                "archived": True,
                "archived_snapshot_at": asset["captured_at"],
            })
        if live_release is not None:
            live_release["assets"].extend(missing_assets)
        else:
            archived_releases.append({
                **{key: archived[key] for key in (
                    "release_id", "tag", "published_at", "prerelease"
                )},
                "url": _releases_url(owner, name),
                "archived": True,
                "archived_snapshot_at": archived["captured_at"],
                "assets": missing_assets,
            })
    archived_releases.sort(key=lambda release: release["published_at"], reverse=True)
    combined.extend(archived_releases)
    return combined, archive["snapshot_at"]


def build_statistics(
    live_releases: list[dict[str, Any]],
    repository: str = DEFAULT_REPOSITORY,
    *,
    history: dict[str, Any] | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    releases, history_snapshot_at = _merge_live_and_history(
        live_releases, repository, history
    )
    total_platforms = _empty_platforms()
    package_total = 0
    total_downloads = 0
    public_releases: list[dict[str, Any]] = []
    for release in releases:
        release_platforms = _empty_platforms()
        release_total = 0
        public_assets: list[dict[str, Any]] = []
        for asset in release["assets"]:
            count = asset["download_count"]
            category = asset["category"]
            release_total = _checked_add(release_total, count, "release total_downloads")
            if category in release_platforms:
                release_platforms[category] = _checked_add(
                    release_platforms[category], count,
                    f"release platforms.{category}",
                )
            public_asset = {
                "name": asset["name"],
                "count": count,
                "category": category,
                "archived": asset["archived"],
            }
            if asset["archived"]:
                public_asset["archived_snapshot_at"] = asset["archived_snapshot_at"]
            public_assets.append(public_asset)
        release_package_total = sum(release_platforms.values())
        if release_package_total > MAX_DOWNLOAD_COUNT:
            raise DownloadStatsError("release package_total exceeded the supported range")
        for platform in PLATFORMS:
            total_platforms[platform] = _checked_add(
                total_platforms[platform], release_platforms[platform],
                f"platforms.{platform}",
            )
        package_total = _checked_add(package_total, release_package_total, "package_total")
        total_downloads = _checked_add(total_downloads, release_total, "total_downloads")
        public_release = {
            "tag": release["tag"],
            "url": release["url"],
            "published_at": release["published_at"],
            "prerelease": release["prerelease"],
            "package_total": release_package_total,
            "total_downloads": release_total,
            "platforms": release_platforms,
            "assets": public_assets,
            "archived": release["archived"],
        }
        if release["archived"]:
            public_release["archived_snapshot_at"] = release["archived_snapshot_at"]
        public_releases.append(public_release)

    result = {
        "schema": 1,
        "repository": repository,
        "generated_at": _timestamp_text(
            generated_at or datetime.now(timezone.utc), "generated_at"
        ),
        "package_total": package_total,
        "total_downloads": total_downloads,
        "platforms": total_platforms,
        "releases": public_releases,
    }
    if history_snapshot_at is not None:
        result["history_snapshot_at"] = history_snapshot_at
    return result


def collect_statistics(
    repository: str = DEFAULT_REPOSITORY,
    *,
    token: str | None = None,
    opener: Callable[..., Any] | None = None,
    generated_at: datetime | None = None,
    history: dict[str, Any] | None = None,
) -> dict[str, Any]:
    live_releases = collect_live_releases(
        repository, token=token, opener=opener
    )
    return build_statistics(
        live_releases,
        repository,
        history=history,
        generated_at=generated_at,
    )


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
    history_path: Path | None = None,
    refresh_history: bool = False,
) -> dict[str, Any]:
    timestamp = generated_at or datetime.now(timezone.utc)
    _timestamp_text(timestamp, "generated_at")
    if refresh_history and history_path is None:
        raise DownloadStatsError("refresh_history requires a history_path")
    if history_path is not None and Path(history_path).resolve() == Path(output).resolve():
        raise DownloadStatsError("history and output paths must be different")

    history: dict[str, Any] | None = None
    if history_path is not None:
        if Path(history_path).exists():
            history = load_history(history_path, repository)
        elif not refresh_history:
            raise DownloadStatsError("download history file is missing")
    live_releases = collect_live_releases(
        repository, token=token, opener=opener
    )
    if refresh_history:
        history = refresh_history_snapshot(
            live_releases,
            repository,
            existing=history,
            captured_at=timestamp,
        )
        write_atomic(Path(history_path), history)
    payload = build_statistics(
        live_releases,
        repository,
        history=history,
        generated_at=timestamp,
    )
    write_atomic(output, payload)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Collect GitHub release asset download counters"
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY)
    parser.add_argument(
        "--history", type=Path, default=DEFAULT_HISTORY,
        help="validated archived counter snapshot",
    )
    parser.add_argument(
        "--refresh-history", action="store_true",
        help="atomically refresh live counters in --history before generating output",
    )
    args = parser.parse_args(argv)
    try:
        generate(
            output=args.output,
            repository=args.repository,
            token=os.environ.get("GITHUB_TOKEN"),
            history_path=args.history,
            refresh_history=args.refresh_history,
        )
    except (DownloadStatsError, OSError) as exc:
        print(f"download statistics failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
