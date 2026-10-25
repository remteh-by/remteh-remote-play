"""Tests for complete, fail-closed GitHub release download statistics."""

from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "download_stats", ROOT / "scripts/download-stats.py"
)
download_stats = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(download_stats)


class FakeResponse(io.BytesIO):
    def __init__(self, payload, *, url, status=200, link=""):
        super().__init__(json.dumps(payload).encode("utf-8"))
        self.status = status
        self.headers = {"Link": link}
        self._url = url

    def getcode(self):
        return self.status

    def geturl(self):
        return self._url


class FixtureAPI:
    def __init__(self, routes):
        self.routes = routes
        self.requests = []

    def __call__(self, request, *, timeout):
        self.requests.append((request, timeout))
        parsed = urllib.parse.urlsplit(request.full_url)
        key = (parsed.path, urllib.parse.parse_qs(parsed.query)["page"][0])
        if key not in self.routes:
            raise AssertionError(f"unexpected API request: {key}")
        value = self.routes[key]
        if isinstance(value, Exception):
            raise value
        payload, status, link = value
        return FakeResponse(payload, url=request.full_url, status=status, link=link)


def page(payload, *, status=200, next_link=False):
    link = '<https://attacker.invalid/not-followed>; rel="next"' if next_link else ""
    return payload, status, link


def release(release_id, tag, *, prerelease=False, draft=False, published="2026-10-25T10:00:00Z"):
    return {
        "id": release_id,
        "tag_name": tag,
        "draft": draft,
        "prerelease": prerelease,
        "published_at": published,
        "html_url": "https://attacker.invalid/forged-release",
        "assets_url": "https://attacker.invalid/forged-assets",
    }


def asset(asset_id, name, count):
    return {"id": asset_id, "name": name, "download_count": count}


class DownloadStatistics(unittest.TestCase):
    def fixture_api(self):
        stable = release(1, "v1.0/rc?")
        preview = release(2, "v1.1-beta", prerelease=True, published="2026-10-25T11:00:00+00:00")
        draft = release(99, "private-draft", draft=True)
        draft["published_at"] = None
        routes = {
            ("/repos/remteh-by/remteh-remote-play/releases", "1"): page(
                [stable, draft], next_link=True
            ),
            ("/repos/remteh-by/remteh-remote-play/releases", "2"): page(
                [stable, preview]
            ),
            ("/repos/remteh-by/remteh-remote-play/releases/1/assets", "1"): page([
                asset(11, "Deckivo-1.0-arm64.apk", 3),
                asset(12, "Deckivo-macos-1.0-b10.zip", 5),
                asset(13, "Deckivo-Linux-1.0-b10-source.zip", 7),
                asset(14, "Deckivo-1.0-kit.zip", 9),
            ], next_link=True),
            ("/repos/remteh-by/remteh-remote-play/releases/1/assets", "2"): page([
                asset(14, "Deckivo-1.0-kit.zip", 9),
                asset(15, "Deckivo-1.0-sources.zip", 2),
                asset(16, "checksums.sha256", 4),
                asset(17, "diagnostics.bin", 6),
            ]),
            ("/repos/remteh-by/remteh-remote-play/releases/2/assets", "1"): page([
                asset(21, "Deckivo-1.1.dmg", 11),
                asset(22, "release-notes.pdf", 1),
                asset(23, "Deckivo-1.1-arm64.apk", 0),
            ]),
        }
        return FixtureAPI(routes)

    def test_aggregates_paginated_stable_and_prerelease_assets(self):
        api = self.fixture_api()
        result = download_stats.collect_statistics(
            opener=api,
            token="secret-token-not-for-output",
            generated_at=datetime(2026, 10, 25, 12, 34, 56, tzinfo=timezone.utc),
        )

        self.assertEqual(result["schema"], 1)
        self.assertEqual(result["repository"], "remteh-by/remteh-remote-play")
        self.assertEqual(result["generated_at"], "2026-10-25T12:34:56Z")
        self.assertEqual(result["platforms"], {
            "android": 3, "macos": 16, "linux": 7, "bundle": 9,
        })
        self.assertEqual(result["package_total"], 35)
        self.assertEqual(result["total_downloads"], 48)
        self.assertEqual(len(result["releases"]), 2)

        stable, preview = result["releases"]
        self.assertEqual(stable["url"], (
            "https://github.com/remteh-by/remteh-remote-play/releases/tag/v1.0%2Frc%3F"
        ))
        self.assertEqual(stable["package_total"], 24)
        self.assertEqual(stable["total_downloads"], 36)
        self.assertEqual(
            {entry["name"]: entry["category"] for entry in stable["assets"]},
            {
                "Deckivo-1.0-arm64.apk": "android",
                "Deckivo-macos-1.0-b10.zip": "macos",
                "Deckivo-Linux-1.0-b10-source.zip": "linux",
                "Deckivo-1.0-kit.zip": "bundle",
                "Deckivo-1.0-sources.zip": "source",
                "checksums.sha256": "metadata",
                "diagnostics.bin": "other",
            },
        )
        self.assertTrue(preview["prerelease"])
        self.assertEqual(preview["package_total"], 11)
        self.assertEqual(preview["total_downloads"], 12)
        self.assertEqual(preview["assets"][2]["count"], 0)

        requested_paths = [urllib.parse.urlsplit(call[0].full_url).path for call in api.requests]
        self.assertNotIn(
            "/repos/remteh-by/remteh-remote-play/releases/99/assets", requested_paths
        )
        self.assertEqual(len(requested_paths), 5)
        self.assertTrue(all(call[0].host == "api.github.com" for call in api.requests))
        self.assertTrue(all(
            call[0].headers.get("Authorization") == "Bearer secret-token-not-for-output"
            for call in api.requests
        ))
        self.assertNotIn("secret-token-not-for-output", json.dumps(result))

    def test_valid_zero_is_written_but_api_failure_preserves_existing_file(self):
        empty_release = release(3, "v0")
        zero_api = FixtureAPI({
            ("/repos/remteh-by/remteh-remote-play/releases", "1"): page([empty_release]),
            ("/repos/remteh-by/remteh-remote-play/releases/3/assets", "1"): page([
                asset(31, "Deckivo-v0.apk", 0)
            ]),
        })
        failing_api = FixtureAPI({
            ("/repos/remteh-by/remteh-remote-play/releases", "1"): page([], status=500),
        })

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "nested/download-stats.json"
            result = download_stats.generate(output, opener=zero_api)
            self.assertEqual(result["package_total"], 0)
            self.assertEqual(json.loads(output.read_text())["total_downloads"], 0)
            before = output.read_bytes()
            with self.assertRaises(download_stats.DownloadStatsError):
                download_stats.generate(output, opener=failing_api)
            self.assertEqual(output.read_bytes(), before)
            self.assertFalse(list(output.parent.glob("*.tmp")))

    def test_malformed_or_malicious_payload_is_rejected(self):
        invalid_assets = (True, -1, "4")
        for invalid_count in invalid_assets:
            with self.subTest(download_count=invalid_count):
                api = FixtureAPI({
                    ("/repos/remteh-by/remteh-remote-play/releases", "1"): page([
                        release(4, "v4")
                    ]),
                    ("/repos/remteh-by/remteh-remote-play/releases/4/assets", "1"): page([
                        asset(41, "Deckivo.apk", invalid_count)
                    ]),
                })
                with self.assertRaises(download_stats.DownloadStatsError):
                    download_stats.collect_statistics(opener=api)

        with self.assertRaises(download_stats.DownloadStatsError):
            download_stats.collect_statistics(
                "remteh-by/../../attacker", opener=lambda *_args, **_kwargs: None
            )
        bad_token = "do-not-print-this\nsecond-header: value"
        with self.assertRaises(download_stats.DownloadStatsError) as caught:
            download_stats.collect_statistics(
                token=bad_token, opener=lambda *_args, **_kwargs: None
            )
        self.assertNotIn("do-not-print-this", str(caught.exception))

    def test_conflicting_duplicate_ids_are_rejected(self):
        rel = release(5, "v5")
        api = FixtureAPI({
            ("/repos/remteh-by/remteh-remote-play/releases", "1"): page([rel]),
            ("/repos/remteh-by/remteh-remote-play/releases/5/assets", "1"): page([
                asset(51, "Deckivo.apk", 1), asset(51, "Deckivo.apk", 2)
            ]),
        })
        with self.assertRaisesRegex(
            download_stats.DownloadStatsError, "conflicting duplicate asset id"
        ):
            download_stats.collect_statistics(opener=api)


if __name__ == "__main__":
    unittest.main(verbosity=2)
