#!/usr/bin/env python3
"""Assemble the Android kit and exact corresponding Android/Mac/Linux sources.

Only Git-tracked project files, required tracked submodule files, and the exact
tracked FetchContent snapshots used by the Android native build are eligible.
Untracked files are never traversed or copied.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import argparse
import configparser
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
ZIP_TIME = (1980, 1, 1, 0, 0, 0)

# These five repositories contributed translation units to the Android arm64
# native library. Their exact gitlinks must be present and initialized.
REQUIRED_SUBMODULES = {
    "android/app/src/main/cpp/oboe": "Android audio backend",
    "third-party/curl": "Android Remote Play HTTP/WebSocket transport",
    "third-party/gf-complete": "Android erasure-coding dependency",
    "third-party/jerasure": "Android erasure-coding dependency",
    "third-party/nanopb": "Android protocol-buffer runtime and generator",
}

# Present in historical .gitmodules or as a gitlink, but not used by the
# Android/Mac/Linux release configuration represented by this kit.
UNUSED_SUBMODULE_REASONS = {
    "test/munit": "excluded: Android native tests are configured OFF",
    "switch/borealis": "excluded: Nintendo Switch homebrew UI is not part of this Android/Mac/Linux kit",
    "third-party/cpp-steam-tools": "excluded: Steam integration is configured OFF",
}

FETCH_SPECS = (
    ("mbedtls", "CMakeLists.txt", "mbedtls"),
    ("json-c", "lib/CMakeLists.txt", "json-c"),
    ("miniupnpc", "lib/CMakeLists.txt", "miniupnpc"),
)

PLATFORM_SOURCE_SENTINELS = {
    "android": "android/app/build.gradle",
    "linux": "desktop/linux/launcher.py",
    "macos": "desktop/macos/build-install.py",
    "license": "COPYING",
    "license_inventory": "LICENSES/DEPENDENCIES.json",
}


class PackagingError(RuntimeError):
    pass


@dataclass(frozen=True)
class SourceEntry:
    component: str
    source: Path
    archive_path: str
    mode: str

    def data(self) -> bytes:
        if self.mode == "120000":
            return os.readlink(self.source).encode("utf-8", "surrogateescape")
        return self.source.read_bytes()


def command(args: list[str], cwd: Path = ROOT, *, text: bool = True) -> str | bytes:
    return subprocess.check_output(args, cwd=cwd, text=text)


def git(repo: Path, *args: str, text: bool = True) -> str | bytes:
    return command(["git", "-C", str(repo), *args], text=text)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_relative(path: str) -> str:
    pure = PurePosixPath(path)
    if pure.is_absolute() or not pure.parts or any(part in ("", ".", "..") for part in pure.parts):
        raise PackagingError(f"Unsafe source path: {path!r}")
    if "\\" in path or "\x00" in path:
        raise PackagingError(f"Non-portable source path: {path!r}")
    return pure.as_posix()


def git_index(repo: Path) -> list[tuple[str, str, str]]:
    """Return mode, object id, path for stage-zero index entries."""
    raw = git(repo, "ls-files", "-s", "-z", text=False)
    rows: list[tuple[str, str, str]] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        header, raw_path = record.split(b"\t", 1)
        mode, object_id, stage = header.decode("ascii").split()
        if stage != "0":
            raise PackagingError(f"Unmerged index entry in {repo}: {os.fsdecode(raw_path)}")
        rows.append((mode, object_id, safe_relative(os.fsdecode(raw_path))))
    return rows


def tracked_changes(repo: Path) -> list[str]:
    output = git(repo, "status", "--porcelain=v1", "--untracked-files=no")
    return [line for line in output.splitlines() if line]


def untracked_count(repo: Path) -> int:
    output = git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    return sum(line.startswith("?? ") for line in output.splitlines())


def root_exclusion(path: str) -> str | None:
    name = PurePosixPath(path).name
    lower = name.lower()
    parts = {part.lower() for part in PurePosixPath(path).parts}
    if lower.endswith(".log"):
        return "tracked build log excluded from corresponding source"
    if lower in {"local.properties", "password.txt", ".env"}:
        raise PackagingError(f"Sensitive local file must never be tracked or packaged: {path}")
    if lower.endswith((".jks", ".keystore", ".p12", ".pfx", ".mobileprovision", ".idsig", ".apk", ".pyc")):
        raise PackagingError(f"Private key, profile, binary, or cache must never be tracked or packaged: {path}")
    if parts.intersection({".gradle", ".cxx", ".buildenv", ".build-tools", "__pycache__", ".private"}):
        raise PackagingError(f"Local cache/private directory must never be tracked or packaged: {path}")
    return None


def entries_for_repo(repo: Path, component: str, archive_prefix: str,
                     *, exclude_root_outputs: bool = False) -> tuple[list[SourceEntry], list[dict], list[dict]]:
    entries: list[SourceEntry] = []
    gitlinks: list[dict] = []
    excluded: list[dict] = []
    for mode, object_id, rel in git_index(repo):
        if mode == "160000":
            gitlinks.append({"path": rel, "revision": object_id})
            continue
        if mode not in {"100644", "100755", "120000"}:
            raise PackagingError(f"Unsupported Git mode {mode} for {component}:{rel}")
        if exclude_root_outputs:
            reason = root_exclusion(rel)
            if reason:
                excluded.append({"path": rel, "reason": reason})
                continue
        source = repo / rel
        if not source.exists() and not source.is_symlink():
            raise PackagingError(f"Tracked source is missing: {source}")
        archive_path = safe_relative(f"{archive_prefix}/{rel}")
        entries.append(SourceEntry(component, source, archive_path, mode))
    return entries, gitlinks, excluded


def inventory(entries: list[SourceEntry]) -> tuple[list[dict], str, int]:
    rows: list[dict] = []
    total = 0
    digest_lines: list[str] = []
    for entry in sorted(entries, key=lambda item: item.archive_path):
        data = entry.data()
        item = {"path": entry.archive_path, "mode": entry.mode, "bytes": len(data), "sha256": sha256(data)}
        rows.append(item)
        total += len(data)
        digest_lines.append(f"{entry.mode} {item['sha256']} {len(data)} {entry.archive_path}\n")
    return rows, sha256("".join(digest_lines).encode()), total


def parse_submodule_declarations() -> dict[str, dict[str, str]]:
    parser = configparser.ConfigParser()
    parser.read(ROOT / ".gitmodules")
    result: dict[str, dict[str, str]] = {}
    for section in parser.sections():
        if not section.startswith("submodule "):
            continue
        path = safe_relative(parser[section]["path"])
        result[path] = {"name": section.split('"', 2)[1], "url": parser[section]["url"]}
    return result


def normalized_git_url(value: str) -> str:
    return value.rstrip("/").removesuffix(".git").lower()


def fetch_declaration(source_file: Path, name: str) -> tuple[str, str]:
    text = source_file.read_text()
    match = re.search(rf"FetchContent_Declare\(\s*{re.escape(name)}\s+(.*?)\n\s*\)", text, re.S)
    if not match:
        raise PackagingError(f"FetchContent declaration for {name} not found in {source_file.relative_to(ROOT)}")
    block = match.group(1)
    repository = re.search(r"GIT_REPOSITORY\s+(\S+)", block)
    tag = re.search(r"GIT_TAG\s+(\S+)", block)
    if not repository or not tag:
        raise PackagingError(f"Incomplete FetchContent declaration for {name}")
    return repository.group(1), tag.group(1)


def find_native_build() -> Path:
    candidates = []
    for dep_base in sorted((ROOT / "android/app/.cxx/RelWithDebInfo").glob("*/arm64-v8a/_deps")):
        native = dep_base.parent
        if all((dep_base / f"{name}-src").is_dir() for name, _, _ in FETCH_SPECS) and \
                (native / "compile_commands.json").is_file() and (native / "android_gradle_build.json").is_file():
            candidates.append(native)
    if len(candidates) != 1:
        shown = [str(path.relative_to(ROOT)) for path in candidates]
        raise PackagingError(f"Expected one complete Android arm64 native build, found {len(candidates)}: {shown}")
    return candidates[0]


def json_c_expected_patch(repo: Path) -> bytes:
    original = git(repo, "show", "HEAD:CMakeLists.txt", text=False)
    expected = original.replace(b"add_subdirectory(apps)", b"# add_subdirectory(apps)")
    expected = expected.replace(b"add_subdirectory(tests)", b"# add_subdirectory(tests)")
    if expected == original:
        raise PackagingError("json-c Android patch no longer changes the declared upstream source")
    return expected


def validate_fetch_worktree(name: str, repo: Path) -> tuple[list[str], int, str | None]:
    changes = tracked_changes(repo)
    patch_sha = None
    if name == "json-c":
        if changes != [" M CMakeLists.txt"]:
            raise PackagingError(f"Unexpected json-c tracked changes: {changes}")
        actual = (repo / "CMakeLists.txt").read_bytes()
        expected = json_c_expected_patch(repo)
        if actual != expected:
            raise PackagingError("json-c CMakeLists.txt does not match the exact Android build patch")
        patch_sha = sha256(git(repo, "diff", "--binary", "HEAD", "--", "CMakeLists.txt", text=False))
    elif changes:
        raise PackagingError(f"Unexpected tracked changes in FetchContent {name}: {changes}")

    untracked = [line[3:] for line in git(repo, "status", "--porcelain=v1", "--untracked-files=all").splitlines()
                 if line.startswith("?? ")]
    if name == "miniupnpc":
        header_dir = repo / "miniupnpc/include"
        expected = {f"miniupnpc/include/miniupnpc/{path.name}" for path in header_dir.glob("*.h")}
        if set(untracked) != expected:
            raise PackagingError(f"Unexpected miniupnpc generated/untracked paths: {sorted(set(untracked) - expected)}")
        for rel in untracked:
            duplicate = repo / rel
            original = header_dir / duplicate.name
            if duplicate.read_bytes() != original.read_bytes():
                raise PackagingError(f"Generated miniupnpc header differs from tracked source: {rel}")
    elif untracked:
        raise PackagingError(f"Unexpected untracked files in FetchContent {name}: {untracked}")
    return changes, len(untracked), patch_sha


def validate_release_inputs(app_version: str, version_code: int) -> dict:
    apk = DIST / f"Deckivo-{app_version}-arm64.apk"
    update_path = DIST / "update.json"
    validation = ROOT / "docs/releases" / f"{app_version}-validation.json"
    required = [apk, update_path, ROOT / "android/app/src/main/assets/remteh-pair-helper.elf",
                ROOT / "README-REMTEH.md", ROOT / "COPYING", ROOT / "ps5-companion/COPYING",
                ROOT / "ATTRIBUTION.md", ROOT / "CHANGELOG.md", ROOT / "scripts/send-helper.py",
                ROOT / "UPSTREAM-LOCK.json"]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise PackagingError(f"Missing release input(s): {missing}")
    update = json.loads(update_path.read_text())
    apk_bytes = apk.stat().st_size
    apk_sha = hashlib.file_digest(apk.open("rb"), "sha256").hexdigest()
    expected = {
        "packageName": "by.remteh.remoteplay",
        "versionName": app_version,
        "versionCode": version_code,
        "minSdk": 26,
        "abi": "arm64-v8a",
        "apkFileName": apk.name,
        "apkBytes": apk_bytes,
        "sha256": apk_sha,
    }
    mismatches = {key: {"expected": value, "actual": update.get(key)} for key, value in expected.items()
                  if update.get(key) != value}
    if update.get("schema") != 1 or mismatches:
        raise PackagingError(f"update.json does not match the signed APK: {mismatches}")
    sdk = Path(os.environ.get("ANDROID_HOME", str(Path.home() / "Library/Android/sdk")))
    apksigner = sdk / "build-tools/36.0.0/apksigner"
    if not apksigner.is_file():
        raise PackagingError(f"apksigner not found: {apksigner}")
    subprocess.run([str(apksigner), "verify", str(apk)], check=True)
    if not validation.is_file():
        raise PackagingError(f"Missing release input(s): ['{validation.relative_to(ROOT)}']")
    try:
        tracked_validation = git(ROOT, "ls-files", "--error-unmatch", str(validation.relative_to(ROOT))).strip()
    except subprocess.CalledProcessError as failure:
        raise PackagingError(f"Release validation must be Git-tracked: {validation.relative_to(ROOT)}") from failure
    if tracked_validation != str(validation.relative_to(ROOT)):
        raise PackagingError(f"Release validation must be Git-tracked: {validation.relative_to(ROOT)}")
    verification = json.loads(validation.read_text())
    if verification.get("version") != app_version or not isinstance(verification.get("android"), dict):
        raise PackagingError("Release validation must identify this version and contain Android evidence")
    verification_android = verification["android"]
    verification_mismatches = {
        key: {"expected": value, "actual": verification_android.get(key)}
        for key, value in expected.items() if verification_android.get(key) != value
    }
    if verification_mismatches:
        raise PackagingError(f"Release validation Android metadata does not match the signed APK: {verification_mismatches}")
    return {"apk": apk, "update": update_path, "validation": validation, "apkBytes": apk_bytes,
            "apkSha256": apk_sha}


def zip_info(name: str, mode: str = "100644") -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(safe_relative(name), ZIP_TIME)
    info.create_system = 3
    permissions = 0o755 if mode == "100755" else 0o777 if mode == "120000" else 0o644
    kind = stat.S_IFLNK if mode == "120000" else stat.S_IFREG
    info.external_attr = (kind | permissions) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    return info


def write_source_archive(path: Path, entries: list[SourceEntry], manifest_bytes: bytes) -> None:
    seen: set[str] = set()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for entry in sorted(entries, key=lambda item: item.archive_path):
            if entry.archive_path in seen:
                raise PackagingError(f"Duplicate source archive path: {entry.archive_path}")
            seen.add(entry.archive_path)
            archive.writestr(zip_info(entry.archive_path, entry.mode), entry.data())
        manifest_name = "source/SOURCE-REVISION.json"
        if manifest_name in seen:
            raise PackagingError(f"Reserved source manifest path is tracked: {manifest_name}")
        archive.writestr(zip_info(manifest_name), manifest_bytes)
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise PackagingError("Source archive CRC verification failed")


def write_file(archive: zipfile.ZipFile, path: Path, name: str, executable: bool = False) -> None:
    archive.writestr(zip_info(name, "100755" if executable else "100644"), path.read_bytes())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="inventory and validate without creating release files")
    args = parser.parse_args()

    subprocess.run([os.environ.get("DECKIVO_BUILD_PYTHON", "python3"),
                    str(ROOT / "scripts/generate-support.py"), "--check"], check=True)
    build_gradle = (ROOT / "android/app/build.gradle").read_text()
    app_version = re.search(r'versionName\s+"([0-9]+\.[0-9]+\.[0-9]+)"', build_gradle).group(1)
    version_code = int(re.search(r"versionCode\s+(\d+)", build_gradle).group(1))
    version = f"Deckivo-{app_version}"

    root_commit = git(ROOT, "rev-parse", "HEAD").strip()
    root_tree = git(ROOT, "rev-parse", "HEAD^{tree}").strip()
    root_changes = tracked_changes(ROOT)
    if root_changes and not args.dry_run:
        raise PackagingError("Tracked worktree must be clean and committed before packaging: " + "; ".join(root_changes))

    root_entries, gitlinks, root_excluded = entries_for_repo(
        ROOT, "project", "source", exclude_root_outputs=True)
    gitlink_map = {row["path"]: row["revision"] for row in gitlinks}
    declarations = parse_submodule_declarations()
    source_entries = list(root_entries)

    root_paths = {entry.archive_path.removeprefix("source/") for entry in root_entries}
    missing_platforms = {platform: path for platform, path in PLATFORM_SOURCE_SENTINELS.items() if path not in root_paths}
    if missing_platforms:
        raise PackagingError(f"Platform/license source sentinel missing from tracked inventory: {missing_platforms}")

    submodule_manifests = []
    for path, purpose in REQUIRED_SUBMODULES.items():
        expected = gitlink_map.get(path)
        if not expected:
            raise PackagingError(f"Required submodule gitlink is missing: {path}")
        repo = ROOT / path
        try:
            actual = git(repo, "rev-parse", "HEAD").strip()
        except subprocess.CalledProcessError as failure:
            raise PackagingError(f"Required submodule is not initialized: {path}") from failure
        if actual != expected:
            raise PackagingError(f"Required submodule revision mismatch for {path}: {actual} != {expected}")
        changes = tracked_changes(repo)
        if changes:
            raise PackagingError(f"Required submodule has tracked changes: {path}: {changes}")
        entries, nested, excluded = entries_for_repo(repo, f"submodule:{path}", f"source/{path}")
        if nested or excluded:
            raise PackagingError(f"Unexpected nested/excluded content in required submodule {path}")
        rows, digest, byte_count = inventory(entries)
        source_entries.extend(entries)
        submodule_manifests.append({
            "path": path, "purpose": purpose, "url": declarations.get(path, {}).get("url"),
            "revision": actual, "tree": git(repo, "rev-parse", "HEAD^{tree}").strip(),
            "trackedClean": True, "untrackedExcluded": untracked_count(repo),
            "fileCount": len(rows), "bytes": byte_count, "inventorySha256": digest, "inventory": rows,
        })

    excluded_submodules = []
    for path, expected in sorted(gitlink_map.items()):
        if path in REQUIRED_SUBMODULES:
            continue
        reason = UNUSED_SUBMODULE_REASONS.get(path)
        if not reason:
            raise PackagingError(f"Tracked submodule has no packaging decision: {path}")
        repo = ROOT / path
        try:
            actual = git(repo, "rev-parse", "HEAD").strip()
        except subprocess.CalledProcessError:
            actual = None
        excluded_submodules.append({"path": path, "url": declarations.get(path, {}).get("url"),
                                    "expectedRevision": expected, "actualRevision": actual, "reason": reason})
    for path, declaration in sorted(declarations.items()):
        if path not in gitlink_map:
            reason = UNUSED_SUBMODULE_REASONS.get(path)
            if not reason:
                raise PackagingError(f"Declared submodule without gitlink has no packaging decision: {path}")
            excluded_submodules.append({"path": path, "url": declaration["url"], "expectedRevision": None,
                                        "actualRevision": None, "reason": reason + "; no gitlink in HEAD"})

    native_build = find_native_build()
    compile_commands = json.loads((native_build / "compile_commands.json").read_text())
    compiled_files = [row["file"] for row in compile_commands]
    native_components = list(REQUIRED_SUBMODULES) + [f"_deps/{name}-src" for name, _, _ in FETCH_SPECS]
    compiled_counts = {component: sum(component in path for path in compiled_files) for component in native_components}
    missing_compiled = [name for name, count in compiled_counts.items() if count == 0]
    if missing_compiled:
        raise PackagingError(f"Required native component did not contribute Android translation units: {missing_compiled}")

    fetch_manifests = []
    dep_base = native_build / "_deps"
    for name, declaration_path, archive_name in FETCH_SPECS:
        repo = dep_base / f"{name}-src"
        declared_url, declared_ref = fetch_declaration(ROOT / declaration_path, name)
        head = git(repo, "rev-parse", "HEAD").strip()
        declared_commit = git(repo, "rev-parse", f"{declared_ref}^{{commit}}").strip()
        if head != declared_commit:
            raise PackagingError(f"FetchContent {name} HEAD {head} does not match declared {declared_ref} ({declared_commit})")
        origin = git(repo, "remote", "get-url", "origin").strip()
        if normalized_git_url(origin) != normalized_git_url(declared_url):
            raise PackagingError(f"FetchContent {name} origin mismatch: {origin} != {declared_url}")
        changes, generated_count, patch_sha = validate_fetch_worktree(name, repo)
        entries, nested, excluded = entries_for_repo(repo, f"fetch:{name}", f"source/vendor/{archive_name}")
        if nested or excluded:
            raise PackagingError(f"Unexpected nested/excluded content in FetchContent {name}")
        rows, digest, byte_count = inventory(entries)
        source_entries.extend(entries)
        fetch_manifests.append({
            "name": name, "archivePath": f"source/vendor/{archive_name}", "declaredIn": declaration_path,
            "repository": declared_url, "declaredRef": declared_ref, "revision": head,
            "tree": git(repo, "rev-parse", "HEAD^{tree}").strip(),
            "trackedBuildPatch": changes, "trackedBuildPatchSha256": patch_sha,
            "generatedUntrackedExcluded": generated_count, "translationUnits": compiled_counts[f"_deps/{name}-src"],
            "fileCount": len(rows), "bytes": byte_count, "inventorySha256": digest, "inventory": rows,
        })

    root_rows, root_digest, root_bytes = inventory(root_entries)
    all_rows, all_digest, all_bytes = inventory(source_entries)
    duplicate_paths = len(all_rows) - len({row["path"] for row in all_rows})
    if duplicate_paths:
        raise PackagingError(f"Source inventory contains {duplicate_paths} duplicate archive paths")

    native_rel = str(native_build.relative_to(ROOT))
    manifest = {
        "schema": 1,
        "project": "Deckivo",
        "version": app_version,
        "sourceArchiveRoot": "source/",
        "root": {
            "commit": root_commit, "tree": root_tree, "trackedClean": not root_changes,
            "trackedChanges": root_changes, "fileCount": len(root_rows), "bytes": root_bytes,
            "inventorySha256": root_digest, "inventory": root_rows,
        },
        "submodules": submodule_manifests,
        "fetchContent": fetch_manifests,
        "androidNativeBuild": {
            "configuration": native_rel, "abi": "arm64-v8a",
            "compileCommandsSha256": hashlib.file_digest((native_build / "compile_commands.json").open("rb"), "sha256").hexdigest(),
            "gradleBuildModelSha256": hashlib.file_digest((native_build / "android_gradle_build.json").open("rb"), "sha256").hexdigest(),
            "translationUnitsByComponent": compiled_counts,
        },
        "excluded": {
            "rootTrackedOutputs": root_excluded,
            "submodules": excluded_submodules,
            "untrackedPolicy": "All untracked project/submodule files are excluded by construction; no filesystem walk is used.",
        },
        "combinedInventory": {"fileCount": len(all_rows), "bytes": all_bytes, "sha256": all_digest},
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()

    release_inputs = None
    release_input_error = None
    try:
        release_inputs = validate_release_inputs(app_version, version_code)
    except PackagingError as failure:
        if not args.dry_run:
            raise
        release_input_error = str(failure)

    ready = not root_changes and release_input_error is None
    summary = {
        "mode": "dry-run" if args.dry_run else "package",
        "version": app_version,
        "rootCommit": root_commit,
        "rootTrackedClean": not root_changes,
        "readyForPackaging": ready,
        "releaseInputError": release_input_error,
        "sourceFiles": len(all_rows),
        "sourceBytes": all_bytes,
        "sourceInventorySha256": all_digest,
        "requiredSubmodules": {row["path"]: row["revision"] for row in submodule_manifests},
        "fetchContent": {row["name"]: {"revision": row["revision"], "inventorySha256": row["inventorySha256"]}
                         for row in fetch_manifests},
        "excludedTrackedOutputs": root_excluded,
        "excludedSubmodules": [{"path": row["path"], "reason": row["reason"]} for row in excluded_submodules],
        "androidNativeTranslationUnits": compiled_counts,
    }
    if args.dry_run:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return
    if not ready or release_inputs is None:
        raise PackagingError("Release source/package inputs are not ready")

    bundle = DIST / version
    package = DIST / f"{version}-kit.zip"
    if bundle.exists() or package.exists():
        raise PackagingError(f"Refusing to overwrite existing package target: {bundle} or {package}")
    DIST.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{version}-package-", dir=DIST) as temp_name:
        temporary = Path(temp_name)
        temp_bundle = temporary / version
        temp_bundle.mkdir()
        source_zip = temp_bundle / f"{version}-sources.zip"
        write_source_archive(source_zip, source_entries, manifest_bytes)
        (temp_bundle / "SOURCE-REVISION.json").write_bytes(manifest_bytes)

        copies = [
            (release_inputs["apk"], release_inputs["apk"].name),
            (release_inputs["update"], "update.json"),
            (ROOT / "android/app/src/main/assets/remteh-pair-helper.elf", "remteh-pair-helper.elf"),
            (ROOT / "README-REMTEH.md", "ИНСТРУКЦИЯ.md"),
            (ROOT / "COPYING", "LICENSE-CHIAKI.txt"),
            (ROOT / "ps5-companion/COPYING", "LICENSE-PS5-HELPER.txt"),
            (ROOT / "ATTRIBUTION.md", "ATTRIBUTION.md"),
            (ROOT / "CHANGELOG.md", "CHANGELOG.md"),
            (ROOT / "scripts/send-helper.py", "send-helper.py"),
            (release_inputs["validation"], "verification.json"),
            (ROOT / "UPSTREAM-LOCK.json", "UPSTREAM-LOCK.json"),
        ]
        for source, name in copies:
            shutil.copy2(source, temp_bundle / name)
        launch = temp_bundle / "Запустить-помощник-PS5.command"
        launch.write_text('''#!/bin/zsh
TASK_DIR="${0:A:h}"
PS5_HOST="${1:-}"
if [[ -z "$PS5_HOST" ]]; then
    printf "IP PS5: "
    read -r PS5_HOST
fi
python3 "$TASK_DIR/send-helper.py" --file "$TASK_DIR/remteh-pair-helper.elf" --host "$PS5_HOST"
HELPER_RESULT=$?
printf '\\nНажми Enter, чтобы закрыть окно.\\n'
read -r REPLY
exit "$HELPER_RESULT"
''')
        launch.chmod(0o755)

        checksums = {}
        for path in sorted(temp_bundle.iterdir()):
            if path.is_file() and path.name != "SHA256SUMS.txt":
                checksums[path.name] = hashlib.file_digest(path.open("rb"), "sha256").hexdigest()
        (temp_bundle / "SHA256SUMS.txt").write_text(
            "".join(f"{digest}  {name}\n" for name, digest in checksums.items()))

        temp_package = temporary / package.name
        with zipfile.ZipFile(temp_package, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for path in sorted(temp_bundle.iterdir()):
                write_file(archive, path, f"{version}/{path.name}", executable=bool(path.stat().st_mode & stat.S_IXUSR))
        with zipfile.ZipFile(temp_package) as archive:
            if archive.testzip() is not None:
                raise PackagingError("Kit archive CRC verification failed")
        shutil.move(temp_bundle, bundle)
        shutil.move(temp_package, package)

    summary.update({
        "kit": str(package), "kitBytes": package.stat().st_size,
        "kitSha256": hashlib.file_digest(package.open("rb"), "sha256").hexdigest(),
        "apkBytes": release_inputs["apkBytes"], "apkSha256": release_inputs["apkSha256"],
    })
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (PackagingError, subprocess.CalledProcessError) as failure:
        raise SystemExit(str(failure)) from failure
