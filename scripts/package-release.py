#!/usr/bin/env python3
"""Assemble user artifacts and corresponding sources; never include signing keys."""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import zipfile

root = Path(__file__).resolve().parents[1]
import subprocess
subprocess.run([os.environ.get('DECKIVO_BUILD_PYTHON','python3'),str(root/'scripts/generate-support.py'),'--check'],check=True)
dist = root / "dist"
app_version = re.search(r'versionName\s+"([0-9]+\.[0-9]+\.[0-9]+)"', (root / "android/app/build.gradle").read_text()).group(1)
version = f"Deckivo-{app_version}"
bundle = dist / version
bundle.mkdir(parents=True, exist_ok=True)
apk = dist / (version + "-arm64.apk")
assert apk.is_file()
for source, name in [
    (apk, apk.name),
    (dist / "update.json", "update.json"),
    (root / "android/app/src/main/assets/remteh-pair-helper.elf", "remteh-pair-helper.elf"),
    (root / "README-REMTEH.md", "ИНСТРУКЦИЯ.md"),
    (root / "COPYING", "LICENSE-CHIAKI.txt"),
    (root / "ps5-companion/COPYING", "LICENSE-PS5-HELPER.txt"),
    (root / "ATTRIBUTION.md", "ATTRIBUTION.md"),
    (root / "CHANGELOG.md", "CHANGELOG.md"),
    (root / "scripts/send-helper.py", "send-helper.py"),
    (root / "docs/releases" / (app_version + "-validation.json"), "verification.json"),
    (root / "UPSTREAM-LOCK.json", "UPSTREAM-LOCK.json"),
]:
    shutil.copy2(source, bundle / name)
command = bundle / "Запустить-помощник-PS5.command"
command.write_text('''#!/bin/zsh
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
command.chmod(0o755)

excluded_dirs = {".git", ".gradle", ".cxx", "build", ".buildenv", ".build-tools", "build-logs", "dist", ".idea", ".kotlin", "__pycache__", ".codex", ".private"}
excluded_files = {"local.properties", ".DS_Store", "companion-host", "password.txt", ".env"}
source_zip = bundle / (version + "-sources.zip")
entries = 0
with zipfile.ZipFile(source_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for folder, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in excluded_dirs)
        for name in sorted(files):
            path = Path(folder) / name
            if name in excluded_files or name == ".git" or name.endswith((".jks", ".keystore", ".apk", ".idsig", ".pyc")):
                continue
            if path == root / "ps5-companion/remteh-pair-helper.elf":
                continue
            archive.write(path, "source/" + str(path.relative_to(root)))
            entries += 1
    # Include exact FetchContent source checkouts, not only URLs/tags.
    dep_bases = list((root / "android/app/.cxx").glob("*/*/arm64-v8a/_deps"))
    dep_base = next((p for p in dep_bases if all((p / (d + "-src")).is_dir() for d in ("mbedtls", "json-c", "miniupnpc"))), None)
    if dep_base is None:
        raise SystemExit("Build native dependencies before packaging their corresponding source")
    for dep in ("mbedtls", "json-c", "miniupnpc"):
        dep_root = dep_base / (dep + "-src")
        for folder, dirs, files in os.walk(dep_root):
            dirs[:] = sorted(d for d in dirs if d not in excluded_dirs)
            for name in sorted(files):
                if name in excluded_files or name == ".git" or name.endswith(".pyc"):
                    continue
                path = Path(folder) / name
                archive.write(path, "source/vendor/" + dep + "/" + str(path.relative_to(dep_root)))
                entries += 1

checksums = {}
for path in sorted(bundle.iterdir()):
    if path.is_file() and path.name != "SHA256SUMS.txt":
        checksums[path.name] = hashlib.file_digest(path.open("rb"), "sha256").hexdigest()
(bundle / "SHA256SUMS.txt").write_text("".join(f"{digest}  {name}\n" for name, digest in checksums.items()))

package = dist / (version + "-kit.zip")
with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for path in sorted(bundle.iterdir()):
        archive.write(path, version + "/" + path.name)
with zipfile.ZipFile(package) as archive:
    assert archive.testzip() is None
with zipfile.ZipFile(source_zip) as archive:
    assert archive.testzip() is None
print(json.dumps({"kit": str(package), "kit_bytes": package.stat().st_size, "source_files": entries,
                  "apk_bytes": apk.stat().st_size, "kit_sha256": hashlib.file_digest(package.open("rb"), "sha256").hexdigest()}, indent=2))
