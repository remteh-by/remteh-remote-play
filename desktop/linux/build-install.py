#!/usr/bin/env python3
"""Install the private Switchroot Ubuntu ARM64 preview without root.

SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
Uses authenticated Ubuntu apt package downloads and a pinned source archive.
Does not upgrade FFmpeg, NVIDIA drivers, firmware, network configuration or saves.
Existing pairing and preferences are retained.
"""
import hashlib
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.request

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent.parent
DEST = Path.home() / '.local/share/deckivo'
SOURCE_URL = 'https://ports.ubuntu.com/pool/universe/c/chiaki/chiaki_2.2.0.orig.tar.gz'
SOURCE_SHA256 = 'b527a8a4c42e694f4eb45403bdc8f1c08da60f1863cc2a768dc6aa174ad6c699'


def run(*args, cwd=None):
    subprocess.run([str(x) for x in args], cwd=cwd, check=True)


def main():
    os.umask(0o077)
    if platform.machine() not in ('aarch64', 'arm64'):
        raise SystemExit('This preview is for Switchroot Ubuntu ARM64 only.')
    if 'VERSION_ID="24.04"' not in Path('/etc/os-release').read_text():
        raise SystemExit('This installer is pinned to Ubuntu 24.04.')
    import PyQt5.QtCore
    import ctypes
    ctypes.CDLL('libavcodec.so.60')
    if not shutil.which('gcc'):
        raise SystemExit('GCC is required to build the local native adapters.')
    runtime = DEST / 'runtime'
    runtime.mkdir(parents=True, exist_ok=True)
    DEST.chmod(0o700)
    packages = ('chiaki=2.2.0-1build3', 'libjerasure2', 'libgf-complete1t64',
                'libjerasure-dev', 'libgf-complete-dev',
                'libavcodec-dev=7:6.1.1-3ubuntu5', 'libavutil-dev=7:6.1.1-3ubuntu5')
    run('apt-get', 'download', *packages, cwd=runtime)
    for deb in runtime.glob('*.deb'):
        run('dpkg-deb', '-x', deb, runtime)
    source_dir = DEST / 'source'
    source_dir.mkdir(exist_ok=True)
    archive = source_dir / 'chiaki_2.2.0.orig.tar.gz'
    if not archive.exists():
        with urllib.request.urlopen(SOURCE_URL, timeout=40) as response:
            archive.write_bytes(response.read())
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise SystemExit('Upstream source SHA-256 did not match. Stopped.')
    with tarfile.open(archive) as tar:
        tar.extractall(source_dir, filter='data')
    source = source_dir / 'chiaki-v2.2.0/lib'
    native = DEST / 'native'
    native.mkdir(exist_ok=True)
    for name in ('register.c', 'tegra-decoder.c','kbm-bridge.c'):
        shutil.copy2(HERE / 'native' / name, native / name)
    include = native / 'include/chiaki'
    include.mkdir(parents=True, exist_ok=True)
    (include / 'config.h').write_text('#define CHIAKI_LIB_ENABLE_MBEDTLS 0\n'
                                    '#define CHIAKI_LIB_VERSION_MAJOR 2\n'
                                    '#define CHIAKI_LIB_VERSION_MINOR 2\n'
                                    '#define CHIAKI_LIB_VERSION_PATCH 0\n')
    text = (source / 'src/session.c').read_text()
    blocks = []
    for name in ('chiaki_rp_version_string', 'chiaki_rp_application_reason_string'):
        index = text.index(name + '(')
        start = text.rfind('\n', 0, index) + 1
        end = text.index('{', index) + 1
        depth = 1
        while depth:
            if text[end] == '{':
                depth += 1
            elif text[end] == '}':
                depth -= 1
            end += 1
        blocks.append(text[start:end])
    (native / 'session_names.c').write_text('#include <chiaki/session.h>\n' + '\n'.join(blocks))
    sources = ('common', 'sock', 'thread', 'base64', 'http', 'log', 'rpcrypt',
               'random', 'stoppipe', 'time', 'regist')
    lib = runtime / 'usr/lib/aarch64-linux-gnu'
    run('gcc', '-O2', '-I' + str(native / 'include'), '-I' + str(source / 'include'),
        '-I' + str(runtime / 'usr/include/jerasure'), '-I' + str(runtime / 'usr/include'),
        native / 'register.c', native / 'session_names.c',
        *[source / 'src' / (name + '.c') for name in sources],
        '-L' + str(lib), '-Wl,-rpath,' + str(lib), '-lJerasure', '-lgf_complete',
        '-lcrypto', '-pthread', '-o', native / 'deckivo-register')
    run('gcc', '-O2', '-fPIC', '-shared',
        '-I' + str(runtime / 'usr/include/aarch64-linux-gnu'),
        native / 'tegra-decoder.c', '-ldl', '-o', native / 'libdeckivo-tegra.so')
    run('gcc','-Wall','-Wextra','-Werror','-O2','-fPIC','-shared',native/'kbm-bridge.c','-ldl','-o',native/'libdeckivo-input.so')
    from upgrade import FILES
    for name in FILES:
        target=DEST/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(HERE/name,target)
    languages = PROJECT / 'localization'
    if languages.is_dir():
        shutil.copytree(languages, DEST / 'localization', dirs_exist_ok=True)
    licenses = PROJECT / 'LICENSES'
    if licenses.is_dir():
        shutil.copytree(licenses, DEST / 'licenses', dirs_exist_ok=True)
    binary = Path.home() / '.local/bin/deckivo'
    binary.parent.mkdir(parents=True, exist_ok=True)
    binary.write_text('#!/bin/sh\nexec /usr/bin/python3 "' + str(DEST / 'deckivo.py') + '" "$@"\n')
    binary.chmod(0o755)
    entry = '[Desktop Entry]\nType=Application\nName=Deckivo\nName[ru]=Deckivo — PS5\n'
    entry += 'Exec=' + str(binary) + '\nIcon=' + str(DEST / 'deckivo.svg')
    entry += '\nTerminal=false\nCategories=Game;Network;\nStartupWMClass=Deckivo Linux\n'
    desktop_path = subprocess.check_output(['xdg-user-dir', 'DESKTOP'], text=True).strip()
    for folder in (Path.home() / '.local/share/applications', Path(desktop_path)):
        folder.mkdir(parents=True, exist_ok=True)
        destination = folder / 'Deckivo.desktop'
        destination.write_text(entry)
        destination.chmod(0o755)
    from update_background import install_user_timer,automatic_enabled
    timer_requested=automatic_enabled();timer_applied=install_user_timer(timer_requested)
    print('Deckivo installed. Existing registration and settings were retained.')
    timer_status='disabled by preference' if not timer_requested else 'enabled' if timer_applied else 'prepared; enable it after login'
    print('Background update timer:',timer_status)
    print('Experimental preview. Pair with: python3 desktop/linux/pair.py')
    print('Audio, input and reconnect acceptance must be checked on your device.')


if __name__ == '__main__':
    main()
