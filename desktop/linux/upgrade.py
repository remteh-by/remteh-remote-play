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
import sys
import tempfile
from session import VERSION

HERE=Path(__file__).resolve().parent
DEST=Path.home()/'.local/share/deckivo'
PRIVATE=Path.home()/'.config/deckivo'
FILES=('deckivo.py','keyboard_mouse.py','input_overlay.py','controller_lab.py','launcher.py','storage.py','session.py','controller.py','ui.py','ui_theme.py',
       'support.py','support_policy.py','updater.py','rsa_verify.py','update_ui.py','install_update.py','build_meta.py','pair.py',
       'update_background.py','upgrade.py',
       'deckivo.svg','README.md','UPSTREAM.json','native/tegra-decoder.c','native/kbm-bridge.c',
       'assets/play-space.svg','assets/ps5-console.png','assets/source.json',
       'assets/fonts/IBMPlexSans.ttf','assets/fonts/OFL.txt','assets/update-public.der','assets/support.json')+tuple('assets/support/'+p.name for p in (HERE/'assets/support').glob('*.svg'))
FILES+=tuple(str(p.relative_to(HERE)) for p in sorted((HERE/'assets/controller-lab').rglob('*')) if p.is_file())
FILES+=('i18n.py','linux_input_settings.py','macos_input_settings.py','assets/desktop-translations.json')
REMOVED=()


def restore_backup(backup):
    backup=Path(backup).resolve()
    backup.relative_to((DEST.parent/'deckivo-backups').resolve())
    receipt=json.loads((backup/'receipt.json').read_text())
    for name in receipt['files']+receipt.get('removed',[]):
        path=Path(name)
        if path.is_absolute() or '..' in path.parts or name=='registration.json' or path.parts[0] in ('runtime','private'):
            raise ValueError('Invalid rollback path')
        target=DEST/path;saved=backup/path
        if name in receipt['previous']:
            if not saved.is_file():raise ValueError('Incomplete rollback backup')
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(saved,target)
        elif target.is_file():target.unlink()


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
            input_library=Path(temp)/'libdeckivo-input.so'
            subprocess.run(['gcc','-Wall','-Wextra','-Werror','-O2','-fPIC','-shared',str(HERE/'native/kbm-bridge.c'),'-ldl','-o',str(input_library)],check=True)
            installed=[];previous=[];removed=[]
            try:
                for name in FILES+('native/libdeckivo-tegra.so','native/libdeckivo-input.so'):
                    source=input_library if name.endswith('libdeckivo-input.so') else library if name.endswith('libdeckivo-tegra.so') else HERE/name
                    target=DEST/name;saved=backup/name
                    saved.parent.mkdir(parents=True,exist_ok=True)
                    if target.exists():shutil.copy2(target,saved);previous.append(name)
                    target.parent.mkdir(parents=True,exist_ok=True)
                    staging=target.with_name(target.name+'.upgrade-new')
                    shutil.copy2(source,staging);staging.replace(target);installed.append(name)
                for name in REMOVED:
                    target=DEST/name;saved=backup/name
                    if target.is_file():
                        saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,saved)
                        target.unlink();previous.append(name);removed.append(name)
                if digest is not None and digest!=hashlib.sha256(registration.read_bytes()).hexdigest():
                    raise RuntimeError('Registration changed unexpectedly.')
            except BaseException:
                for name in reversed(installed+removed):
                    saved,target=backup/name,DEST/name
                    if saved.exists():shutil.copy2(saved,target)
                    else:target.unlink(missing_ok=True)
                raise
        receipt={'upgraded_to':VERSION,'files':list(installed),'removed':removed,
            'previous':previous,'pairing_retained':True}
        (backup/'receipt.json').write_text(json.dumps(receipt,indent=2))
        try:
            from update_background import install_user_timer,automatic_enabled
            receipt['background_timer_prepared']=install_user_timer(None if '--json' in sys.argv else automatic_enabled())
        except Exception:
            # Timer setup is repairable on the next launch and must never turn a
            # completed client-file transaction into a half-reported failure.
            receipt['background_timer_prepared']=False
        (backup/'receipt.json').write_text(json.dumps(receipt,indent=2))
        if '--json' not in sys.argv:
            print('Deckivo '+VERSION+' installed. Pairing and preferences retained.')
            print('Rollback files:',backup)
        return {'backup':str(backup),'version':VERSION,'pairing_retained':True}


if __name__=='__main__':
    result=main()
    if '--json' in sys.argv:print(json.dumps(result))
