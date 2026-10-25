#!/usr/bin/env python3
"""Generate update.json from the actual signed APK, never a hand-entered version/hash."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("apk", type=Path)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
sdk = Path(os.environ.get("ANDROID_HOME", str(Path.home() / "Library/Android/sdk")))
tools = sdk / "build-tools/36.0.0"
subprocess.run([str(tools / "apksigner"), "verify", str(args.apk)], check=True)
badging = subprocess.check_output([str(tools / "aapt2"), "dump", "badging", str(args.apk)], text=True)
package = re.search(r"package: name='([^']+)' versionCode='([0-9]+)' versionName='([^']+)'", badging)
minimum = re.search(r"^(?:minSdkVersion|sdkVersion):'([0-9]+)'", badging, re.M)
abi = re.search(r"^native-code: (.+)$", badging, re.M)
assert package and minimum and abi, "APK metadata missing"
name, code, version = package.groups()
assert name == "by.remteh.remoteplay" and re.fullmatch(r"[0-9]+[.][0-9]+[.][0-9]+", version)
assert abi.group(1).strip() == "'arm64-v8a'", "Updater currently distributes arm64 only"
assert args.apk.name == f"Deckivo-{version}-arm64.apk"
size = args.apk.stat().st_size
assert 0 < size <= 100 * 1024 * 1024
with args.apk.open("rb") as stream:
    digest = hashlib.file_digest(stream, "sha256").hexdigest()
manifest = dict(schema=1, packageName=name, versionName=version, versionCode=int(code),
                minSdk=int(minimum.group(1)), abi="arm64-v8a", apkFileName=args.apk.name,
                apkBytes=size, sha256=digest)
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps(manifest, indent=2))
