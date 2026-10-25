#!/usr/bin/env python3
"""Upgrade an existing Deckivo Switchroot installation without root or apt.

Builds in a temporary directory, retains a versioned rollback copy, and never
copies registration/preferences into the distributable source directory.
"""
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import tempfile
from session import VERSION

HERE=Path(__file__).resolve().parent
DEST=Path.home()/'.local/share/deckivo'
PRIVATE=Path.home()/'.config/deckivo'
FILES=('deckivo.py','launcher.py','storage.py','session.py','controller.py','ui.py','ui_theme.py',
       'updater.py','update_ui.py','install_update.py','build_meta.py','pair.py',
       'deckivo.svg','README.md','UPSTREAM.json','native/tegra-decoder.c',
       'assets/ps5-console.png','assets/source.json','assets/NOTICE.txt',
       'assets/fonts/IBMPlexSans.ttf','assets/fonts/OFL.txt','assets/update-public.der')


def main():
    os.umask(0o077)
    if platform.machine() not in ('aarch64','arm64'):
        raise SystemExit('This upgrade is for the existing Switchroot Ubuntu ARM64 preview.')
    runtime=DEST/'runtime'
    if not (runtime/'usr/bin/chiaki').is_file():
        raise SystemExit('Install the initial runtime with build-install.py first.')
    from PyQt5.QtCore import QLockFile
    PRIVATE.mkdir(parents=True,exist_ok=True);PRIVATE.chmod(0o700)
    application_lock=QLockFile(str(PRIVATE/'application.lock'))
    if not application_lock.tryLock(0):
        raise SystemExit('Close Deckivo before upgrading. The launcher is still running.')
    # A running launcher can still be using old code. Ask it to close first.
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as control:
        control.settimeout(.5)
        try:control.connect(str(PRIVATE/'launcher.sock'))
        except OSError:pass
        else:raise SystemExit('Close Deckivo before upgrading. An active stream is never interrupted.')
    with (PRIVATE/'stream.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise SystemExit('A streaming engine is running. Close the stream first.')
        registration=DEST/'registration.json'
        digest=hashlib.sha256(registration.read_bytes()).hexdigest() if registration.exists() else None
        timestamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        backup=DEST.parent/'deckivo-backups'/('before-'+VERSION+'-'+timestamp);backup.mkdir(parents=True,exist_ok=False);backup.chmod(0o700)
        with tempfile.TemporaryDirectory(prefix='deckivo-build-') as temp:
            library=Path(temp)/'libdeckivo-tegra.so'
            subprocess.run(['gcc','-Wall','-Wextra','-O2','-fPIC','-shared',
                '-I'+str(runtime/'usr/include/aarch64-linux-gnu'),
                str(HERE/'native/tegra-decoder.c'),'-ldl','-o',str(library)],check=True)
            installed=[]
            try:
                for name in FILES+('native/libdeckivo-tegra.so',):
                    source=library if name.endswith('.so') else HERE/name
                    target=DEST/name;saved=backup/name
                    saved.parent.mkdir(parents=True,exist_ok=True)
                    if target.exists():shutil.copy2(target,saved)
                    target.parent.mkdir(parents=True,exist_ok=True)
                    staging=target.with_name(target.name+'.upgrade-new')
                    shutil.copy2(source,staging);staging.replace(target);installed.append(name)
                if digest is not None and digest!=hashlib.sha256(registration.read_bytes()).hexdigest():
                    raise RuntimeError('Registration changed unexpectedly.')
            except BaseException:
                for name in reversed(installed):
                    saved,target=backup/name,DEST/name
                    if saved.exists():shutil.copy2(saved,target)
                    else:target.unlink(missing_ok=True)
                raise
        (backup/'receipt.json').write_text(json.dumps({'upgraded_to':VERSION,
            'files':list(installed),'pairing_retained':True},indent=2))
        print('Deckivo '+VERSION+' installed. Pairing and preferences retained.')
        print('Rollback files:',backup)
        print('Open Deckivo and test video, sound, GameSir, disconnect and reconnect.')


if __name__=='__main__':main()
