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
from build_meta import BUILD

LINUX_PLATFORM = 'linux-switch-arm64'
PINNED_PUBLIC_KEY = ROOT / 'design-system/update-public.der'
LINUX_RELEASE_DOCUMENTS = (
    'COPYING',
    'ATTRIBUTION.md',
    'LICENSES/AGPL-3.0-only-OpenSSL.txt',
    'LICENSES/ATTRIBUTION.md',
    'LICENSES/COPYING',
    'LICENSES/DEPENDENCIES.json',
    'LICENSES/DualShockTools-MIT.txt',
    'LICENSES/PYTHON-LICENSE.txt',
    'LICENSES/PyInstaller/0-COPYING.txt',
    'LICENSES/PyQt5-Qt5/0-LICENSE',
    'LICENSES/PyQt5-sip/0-LICENSE',
    'LICENSES/PyQt5/GPL-3.0.txt',
    'LICENSES/SOURCE-LOCATIONS.md',
    'LICENSES/truststore/0-LICENSE',
)


def metadata(path, platform, build):
    return dict(platform=platform, version=VERSION, build=build,
        filename=path.name, bytes=path.stat().st_size,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        url=f'https://github.com/remteh-by/remteh-remote-play/releases/download/v{VERSION}/{path.name}')


def verified_packages(feed, public_key=PINNED_PUBLIC_KEY):
    """Read an existing feed only after authenticating its exact bytes."""
    from rsa_verify import verify
    payload = (feed / 'index.json').read_bytes()
    signature = (feed / 'index.sig').read_bytes()
    verify(payload, signature, public_key.read_bytes())
    document = json.loads(payload)
    packages = document.get('packages') if isinstance(document, dict) and document.get('schema') == 1 else None
    if not isinstance(packages, list) or not all(isinstance(row, dict) and isinstance(row.get('platform'), str) for row in packages):
        raise ValueError('Existing update feed is invalid')
    return packages


def replace_linux_package(packages, replacement):
    if replacement.get('platform') != LINUX_PLATFORM:
        raise ValueError('Replacement is not a Linux package')
    return [row for row in packages if row['platform'] != LINUX_PLATFORM] + [replacement]


def build_linux_archive(target):
    if len(FILES) != len(set(FILES)):
        raise ValueError('Linux package file list contains duplicates')
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in FILES:
            archive.write(ROOT / 'desktop/linux' / name, 'desktop/linux/' + name)
        for name in LINUX_RELEASE_DOCUMENTS:
            archive.write(ROOT / name, name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mac-app', type=Path)
    parser.add_argument('--linux-only', action='store_true')
    parser.add_argument('--build', type=int, required=True)
    parser.add_argument('--signing-key', type=Path, required=True)
    args = parser.parse_args()
    if args.linux_only and args.mac_app is not None:
        parser.error('--mac-app cannot be used with --linux-only')
    if not args.linux_only and args.mac_app is None:
        parser.error('--mac-app is required unless --linux-only is used')
    if args.build != BUILD:raise SystemExit('Public package build must equal source BUILD')
    subprocess.run([sys.executable,str(ROOT/'scripts/generate-support.py'),'--check'],check=True)
    dist = ROOT / 'dist'
    dist.mkdir(exist_ok=True)
    feed = ROOT / 'website/updates'
    packages = []
    if args.linux_only:
        existing_packages = verified_packages(feed)
    else:
        with tempfile.TemporaryDirectory(prefix='deckivo-public-') as name:
            stage = Path(name) / 'Deckivo.app'
            shutil.copytree(args.mac_app, stage, symlinks=True)
            info_path = stage / 'Contents/Info.plist'
            info = plistlib.loads(info_path.read_bytes())
            if info.get('CFBundleIdentifier') != 'by.remteh.deckivo' or info.get('CFBundleShortVersionString') != VERSION:
                raise SystemExit('Staged app does not match this source version.')
            if args.build != int(info['CFBundleVersion']):
                raise SystemExit('Staging bundle build must equal source BUILD.')
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
    build_linux_archive(target)
    linux_package = metadata(target, LINUX_PLATFORM, args.build)
    packages = replace_linux_package(existing_packages, linux_package) if args.linux_only else packages + [linux_package]
    feed.mkdir(exist_ok=True)
    payload = json.dumps(dict(schema=1, packages=packages), separators=(',', ':'), sort_keys=True).encode()
    (feed / 'index.json').write_bytes(payload)
    signature = subprocess.run(['openssl', 'dgst', '-sha256', '-sign', str(args.signing_key),
        str(feed / 'index.json')], check=True, capture_output=True).stdout
    (feed / 'index.sig').write_bytes(base64.b64encode(signature))
    print(json.dumps(packages, indent=2))


if __name__ == '__main__':
    main()
