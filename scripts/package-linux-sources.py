#!/usr/bin/env python3
"""Create the Linux corresponding-source archive from one exact Git commit.

The Linux update is Python/source assets plus two C adapters compiled on the
device. It does not distribute the Ubuntu Chiaki engine or repository
submodules. Only an explicit allowlist of tracked Git blobs is archived.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = (
    'ATTRIBUTION.md',
    'BUILDING.md',
    'CHANGELOG.md',
    'COPYING',
    'README.md',
    'README-REMTEH.md',
    'RELEASING.md',
    'UPSTREAM-LOCK.json',
)
SOURCE_PREFIXES = (
    'LICENSES/',
    'desktop/linux/',
    'docs/',
)
BUILD_CONTROL_FILES = (
    'scripts/generate-desktop-localizations.py',
    'localization/desktop.json',
    'scripts/generate-support.py',
    'scripts/package-linux-sources.py',
    'scripts/package-public-release.py',
    'design-system/support.json',
    'design-system/supporters.json',
    'design-system/update-public.der',
    'localization/support.json',
    'android/app/src/main/res/raw/deckivo_support.json',
    'website/support.json',
    'website/updates/index.json',
    'website/updates/index.sig',
)
FORBIDDEN_PARTS = {
    '.git', '.gradle', '.cxx', '.buildenv', '.build-tools', 'build-logs',
    'dist', '__pycache__', '.private', '.codex',
}
FORBIDDEN_NAMES = {
    '.env', 'local.properties', 'password.txt', 'registration.json',
    'preferences.json', 'update-channel.json', 'update-ack.json',
    'update-receipt.json', 'update-error.json',
}
FORBIDDEN_SUFFIXES = ('.log', '.pyc', '.pyo', '.jks', '.keystore', '.apk', '.idsig')


def git(*arguments, text=False):
    return subprocess.check_output(['git', *arguments], cwd=ROOT, text=text)


def commit_blob(revision, path):
    return git('show', revision + ':' + path, text=True)


def version_build(revision):
    session = commit_blob(revision, 'desktop/linux/session.py')
    build_meta = commit_blob(revision, 'desktop/linux/build_meta.py')
    version = re.search(r"^VERSION\s*=\s*'([0-9]+\.[0-9]+\.[0-9]+)'", session, re.MULTILINE)
    build = re.search(r'^BUILD\s*=\s*([0-9]+)', build_meta, re.MULTILINE)
    if not version or not build:
        raise SystemExit('Cannot read Linux version/build from the selected commit')
    return version.group(1), int(build.group(1))


def tree_entries(revision):
    entries = []
    for raw in git('ls-tree', '-rz', '--full-tree', revision).split(b'\0'):
        if not raw:
            continue
        metadata, encoded_path = raw.split(b'\t', 1)
        mode, kind, object_id = metadata.decode().split(' ')
        path = encoded_path.decode('utf-8')
        entries.append((mode, kind, object_id, path))
    return entries


def selected_blobs(entries):
    exact = set(ROOT_FILES + BUILD_CONTROL_FILES)
    selected = []
    available = {path for _, kind, _, path in entries if kind == 'blob'}
    missing = sorted(exact - available)
    if missing:
        raise SystemExit('Required tracked source files are missing: ' + ', '.join(missing))
    for mode, kind, object_id, path in entries:
        if kind != 'blob':
            continue
        if path not in exact and not path.startswith(SOURCE_PREFIXES):
            continue
        parts = Path(path).parts
        if (any(part in FORBIDDEN_PARTS for part in parts)
                or Path(path).name in FORBIDDEN_NAMES or path.endswith(FORBIDDEN_SUFFIXES)):
            raise SystemExit('Forbidden source path selected: ' + path)
        selected.append((mode, object_id, path))
    return sorted(selected, key=lambda row: row[2])


def revision_manifest(revision, tree, version, build, files, gitlinks):
    return {
        'schema': 1,
        'product': 'Deckivo',
        'platform': 'linux-switch-arm64',
        'version': version,
        'build': build,
        'git_revision': revision,
        'git_tree': tree,
        'archive_root': 'source/',
        'tracked_allowlist': {
            'root_files': list(ROOT_FILES),
            'prefixes': list(SOURCE_PREFIXES),
            'build_control_files': list(BUILD_CONTROL_FILES),
        },
        'files': files,
        'dependency_sources': {
            'included_submodules': [],
            'excluded_repository_submodules': [
                {'path': path, 'git_revision': object_id,
                 'reason': 'not used or distributed by the Linux source update'}
                for _, _, object_id, path in gitlinks
            ],
            'distributed_engine': False,
            'engine_note': ('The update does not contain Chiaki or another streaming engine. '
                            'The existing Ubuntu chiaki 2.2.0-1build3 runtime is retained.'),
            'external_engine_source': {
                'url': 'https://ports.ubuntu.com/pool/universe/c/chiaki/chiaki_2.2.0.orig.tar.gz',
                'sha256': 'b527a8a4c42e694f4eb45403bdc8f1c08da60f1863cc2a768dc6aa174ad6c699',
                'included': False,
            },
            'system_build_dependencies': [
                'Ubuntu 24.04 Python 3 and PyQt5',
                'GCC and glibc/libdl/pthread/Linux headers',
                'Ubuntu FFmpeg 6 development headers and runtime libraries',
                'SDL2 provided by the retained Ubuntu Chiaki runtime',
            ],
        },
    }


def zip_info(name, timestamp, executable=False):
    info = zipfile.ZipInfo(name, timestamp)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = ((0o100755 if executable else 0o100644) << 16)
    return info


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--revision', required=True, help='Exact 40-character source commit SHA')
    parser.add_argument('--version', required=True)
    parser.add_argument('--build', required=True, type=int)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[0-9a-f]{40}', args.revision):
        raise SystemExit('--revision must be an exact lowercase 40-character commit SHA')
    revision = git('rev-parse', '--verify', args.revision + '^{commit}', text=True).strip()
    if revision != args.revision:
        raise SystemExit('Selected revision did not resolve exactly')
    head = git('rev-parse', 'HEAD', text=True).strip()
    if head != revision:
        raise SystemExit('Check out the exact source revision before packaging')
    if git('status', '--porcelain', '--untracked-files=no').strip():
        raise SystemExit('Commit tracked changes before packaging corresponding sources')
    output = args.output.resolve()
    if output.exists():
        raise SystemExit('Output already exists; source archives are never overwritten')
    output.parent.mkdir(parents=True, exist_ok=True)

    entries = tree_entries(revision)
    selected = selected_blobs(entries)
    gitlinks = [entry for entry in entries if entry[1] == 'commit']
    version, build = version_build(revision)
    if (version, build) != (args.version, args.build):
        raise SystemExit(f'Source is {version} build {build}, not {args.version} build {args.build}')
    tree = git('rev-parse', revision + '^{tree}', text=True).strip()
    commit_time = int(git('show', '-s', '--format=%ct', revision, text=True).strip())
    moment = datetime.datetime.fromtimestamp(commit_time, datetime.timezone.utc)
    timestamp = (max(1980, moment.year), moment.month, moment.day,
                 moment.hour, moment.minute, moment.second - moment.second % 2)
    inventory = []
    blobs = []
    for mode, object_id, path in selected:
        data = git('cat-file', 'blob', object_id)
        blobs.append((mode, path, data))
        inventory.append({'path': path, 'git_blob': object_id,
                          'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
    manifest = revision_manifest(revision, tree, version, build, inventory, gitlinks)
    manifest_data = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode()

    with zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for mode, path, data in blobs:
            archive.writestr(zip_info('source/' + path, timestamp, mode == '100755'), data)
        archive.writestr(zip_info('source/SOURCE-REVISION.json', timestamp), manifest_data)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise SystemExit('Source archive integrity check failed')
        names = archive.namelist()
        if len(names) != len(set(names)) or names[-1] != 'source/SOURCE-REVISION.json':
            raise SystemExit('Source archive inventory is invalid')
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    print(json.dumps({'archive': str(output), 'version': version, 'build': build,
        'git_revision': revision, 'git_tree': tree, 'source_files': len(inventory),
        'bytes': output.stat().st_size, 'sha256': digest, 'submodules_included': []}, indent=2))


if __name__ == '__main__':
    main()
