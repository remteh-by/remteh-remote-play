#!/usr/bin/env python3
"""Prepare exact native assets and RSA-signed public metadata, without uploading.

Private keys stay outside Git. Source/validation/SHA256SUMS are packaged separately.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'desktop/linux'))
from session import VERSION
from upgrade import FILES


def metadata(path, platform, build):
    return dict(platform=platform, version=VERSION, build=build,
        filename=path.name, bytes=path.stat().st_size,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        url=f'https://github.com/remteh-by/remteh-remote-play/releases/download/v{VERSION}/{path.name}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mac-app', type=Path, required=True)
    parser.add_argument('--build', type=int, required=True)
    parser.add_argument('--signing-key', type=Path, required=True)
    args = parser.parse_args()
    dist = ROOT / 'dist'
    dist.mkdir(exist_ok=True)
    packages = []
    with tempfile.TemporaryDirectory(prefix='deckivo-public-') as name:
        stage = Path(name) / 'Deckivo.app'
        shutil.copytree(args.mac_app, stage, symlinks=True)
        info_path = stage / 'Contents/Info.plist'
        info = plistlib.loads(info_path.read_bytes())
        if info.get('CFBundleIdentifier') != 'by.remteh.deckivo' or info.get('CFBundleShortVersionString') != VERSION:
            raise SystemExit('Staged app does not match this source version.')
        if args.build <= int(info['CFBundleVersion']):
            raise SystemExit('Use a build newer than the staging bundle.')
        info['CFBundleVersion'] = str(args.build)
        info_path.write_bytes(plistlib.dumps(info))
        shutil.copytree(ROOT / 'LICENSES', stage / 'Contents/Resources/licenses', dirs_exist_ok=True)
        subprocess.run(['codesign', '--force', '--deep', '--sign', '-', str(stage)], check=True)
        subprocess.run(['codesign', '--verify', '--deep', '--strict', str(stage)], check=True)
        target = dist / f'Deckivo-macos-{VERSION}-b{args.build}.zip'
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
            for folder, dirs, files in os.walk(stage, followlinks=False):
                for leaf in sorted(dirs + files):
                    path = Path(folder) / leaf
                    relative = str(path.relative_to(stage.parent))
                    if path.is_symlink():
                        entry = zipfile.ZipInfo(relative)
                        entry.external_attr = (stat.S_IFLNK | 0o777) << 16
                        archive.writestr(entry, os.readlink(path))
                    elif path.is_file():
                        archive.write(path, relative)
        packages.append(metadata(target, 'macos-arm64', args.build))
    target = dist / f'Deckivo-Linux-{VERSION}-b{args.build}-source.zip'
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in FILES + ('upgrade.py',):
            if name == 'build_meta.py':
                archive.writestr('desktop/linux/' + name, 'BUILD = ' + str(args.build) + '\n')
            else:
                archive.write(ROOT / 'desktop/linux' / name, 'desktop/linux/' + name)
    packages.append(metadata(target, 'linux-switch-arm64', args.build))
    feed = ROOT / 'website/updates'
    feed.mkdir(exist_ok=True)
    payload = json.dumps(dict(schema=1, packages=packages), separators=(',', ':'), sort_keys=True).encode()
    (feed / 'index.json').write_bytes(payload)
    signature = subprocess.run(['openssl', 'dgst', '-sha256', '-sign', str(args.signing_key),
        str(feed / 'index.json')], check=True, capture_output=True).stdout
    (feed / 'index.sig').write_bytes(base64.b64encode(signature))
    print(json.dumps(packages, indent=2))


if __name__ == '__main__':
    main()
