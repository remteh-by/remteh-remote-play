"""Read-only requirements check for the Switchroot installer; no OS mutations."""
import argparse
import ctypes.util
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import sys


def facts(destination=None):
    destination = destination or Path.home() / '.local/share/deckivo'
    parent = destination
    while not parent.exists():
        parent = parent.parent
    release = {}
    try:
        for line in Path('/etc/os-release').read_text().splitlines():
            if '=' in line:
                key, value = line.split('=', 1)
                release[key] = value.strip('"')
    except OSError:
        pass
    return {
        'system': platform.system(), 'architecture': platform.machine(),
        'os_id': release.get('ID', ''), 'os_version': release.get('VERSION_ID', ''),
        'python': list(sys.version_info[:2]), 'qt': importlib.util.find_spec('PyQt5') is not None,
        'display': bool(os.environ.get('DISPLAY')), 'session': os.environ.get('XDG_SESSION_TYPE', ''),
        'free_bytes': shutil.disk_usage(parent).free, 'writable': os.access(parent, os.W_OK),
        'commands': {name: bool(shutil.which(name)) for name in ('gcc', 'apt-get', 'dpkg-deb')},
        'avcodec': ctypes.util.find_library('avcodec') or '',
        'crypto': bool(ctypes.util.find_library('crypto')), 'sdl2': bool(ctypes.util.find_library('SDL2')),
        'existing_runtime': (destination / 'runtime/usr/bin/chiaki').is_file(),
    }


def evaluate(value):
    checks = []
    def check(name, passed, action):
        checks.append({'check': name, 'passed': bool(passed), 'action': '' if passed else action})
    check('Switchroot Linux ARM64', value['system'] == 'Linux' and value['architecture'] in ('arm64', 'aarch64'), 'Use the prepared Switchroot Ubuntu ARM64 device. A Mac/x64 check does not validate that device.')
    check('Ubuntu 24.04', value['os_id'] == 'ubuntu' and value['os_version'] == '24.04', 'This installer targets Ubuntu 24.04. Do not upgrade or replace the OS to satisfy this check.')
    check('Python 3.12+', tuple(value['python']) >= (3, 12), 'Run with Ubuntu 24.04 system Python 3.12 or later.')
    check('PyQt5', value['qt'], 'Install the documented PyQt5 prerequisite in the supported environment.')
    check('X11 desktop', value['display'] and value['session'] != 'wayland', 'Run from a terminal in the KDE/X11 desktop; do not use a Wayland session.')
    check('FFmpeg 6.1 ABI', value['avcodec'] == 'libavcodec.so.60', 'Switchroot libavcodec.so.60 is required. Do not replace Tegra/FFmpeg drivers with generic packages.')
    check('OpenSSL and SDL2', value['crypto'] and value['sdl2'], 'Verify the documented OpenSSL/SDL2 prerequisites without replacing graphics drivers.')
    check('Build tools', all(value['commands'].values()), 'GCC, apt-get and dpkg-deb must be available; review prerequisites.')
    check('Free space', value['free_bytes'] >= 2 * 1024**3, 'Free at least 2 GiB in the target filesystem.')
    check('User directory writable', value['writable'], 'Use the normal desktop user and a writable home directory; do not run the installer as root.')
    check('First installation', not value['existing_runtime'], 'An existing runtime is present. Use the signed update or upgrade.py, which preserves a rollback copy.')
    return checks


def run(destination=None):
    result = evaluate(facts(destination))
    for row in result:
        print(('OK: ' if row['passed'] else 'STOP: ') + row['check'])
        if row['action']:
            print('  ' + row['action'])
    return all(row['passed'] for row in result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    if args.json:
        results = evaluate(facts())
        print(json.dumps({'schema': 1, 'checks': results}, indent=2))
        sys.exit(0 if all(row['passed'] for row in results) else 1)
    sys.exit(0 if run() else 1)
