#!/usr/bin/env python3
"""Stage signed Deckivo updates from a systemd user timer without opening the UI."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from PyQt5.QtCore import QLockFile

from build_meta import BUILD
from session import VERSION,preferences
from storage import HERE,PRIVATE,CONFIG,load_json,private_json
from updater import (UpdateBusy,channel_base,check_and_download,update_lock,
                     validate_staged)


CACHE=PRIVATE/'updates'
PENDING=CACHE/'pending.json'
STATUS=PRIVATE/'update-background.json'
SERVICE_NAME='deckivo-update.service'
TIMER_NAME='deckivo-update.timer'
LOGIN_TIMER_NAME='deckivo-update-login.timer'
USER_UNIT_DIR=Path.home()/'.config/systemd/user'


def record(state,**values):
    private_json(STATUS,dict(state=state,time=int(time.time()),**values))


def application_running():
    lock=QLockFile(str(PRIVATE/'application.lock'))
    if not lock.tryLock(0):return True
    lock.unlock();return False


def automatic_enabled():return preferences(load_json(CONFIG,{})).get('automatic_updates',True)


def stage_update():
    os.umask(0o077)
    if not automatic_enabled():
        record('disabled');return None
    if application_running():
        record('deferred',reason='Deckivo is open');return None
    base=channel_base(load_json(PRIVATE/'update-channel.json',{}))
    try:
        with update_lock(CACHE):
            pending=load_json(PENDING,{})
            try:
                ready=validate_staged(pending,'linux-switch-arm64',VERSION,BUILD,CACHE,HERE/'assets/update-public.der')
            except (OSError,ValueError,KeyError,TypeError):ready=None
            if ready:
                entry=ready['entry'];record('ready',version=entry['version'],build=entry['build'])
                return ready
            ready=check_and_download(base,'linux-switch-arm64',VERSION,BUILD,CACHE,
                HERE/'assets/update-public.der',locked=True)
            private_json(PRIVATE/'update-last-success.json',{'time':time.time(),'version':VERSION,'build':BUILD})
            if ready:
                private_json(PENDING,ready)
                entry=ready['entry'];record('ready',version=entry['version'],build=entry['build'])
            else:
                PENDING.unlink(missing_ok=True)
                record('current',version=VERSION,build=BUILD)
            return ready
    except UpdateBusy:
        record('busy');return None
    except Exception as error:
        record('failed',error=str(error)[:300]);return None


def unit_text():
    service='''[Unit]
Description=Check for signed Deckivo updates

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 %h/.local/share/deckivo/update_background.py --check
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=%h/.config/deckivo
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
'''
    timer='''[Unit]
Description=Check for Deckivo updates while the user is logged in

[Timer]
OnUnitInactiveSec=60min
AccuracySec=1min
RandomizedDelaySec=10min
Unit=deckivo-update.service

[Install]
WantedBy=timers.target
'''
    login_timer = """[Unit]
Description=Check Deckivo updates shortly after user login

[Timer]
OnStartupSec=45s
AccuracySec=1s
RandomizedDelaySec=0
Unit=deckivo-update.service

[Install]
WantedBy=timers.target
"""
    return service,timer,login_timer


def write_unit(path,text):
    path.parent.mkdir(parents=True,exist_ok=True);path.parent.chmod(0o700)
    if path.exists() and path.read_text()==text:return False
    temporary=path.with_suffix(path.suffix+'.tmp')
    descriptor=os.open(temporary,os.O_CREAT|os.O_TRUNC|os.O_WRONLY,0o600)
    with os.fdopen(descriptor,'w') as output:
        output.write(text);output.flush();os.fsync(output.fileno())
    temporary.replace(path);path.chmod(0o600);return True


def install_user_timer(enable=True):
    os.umask(0o077)
    if not sys.platform.startswith('linux'):return False
    directory=USER_UNIT_DIR;service,timer,login_timer=unit_text()
    try:
        changed=write_unit(directory/SERVICE_NAME,service)
        changed=write_unit(directory/TIMER_NAME,timer) or changed
        changed=write_unit(directory/LOGIN_TIMER_NAME,login_timer) or changed
    except OSError:return False
    if enable is None:return True
    systemctl=shutil.which('systemctl')
    if not systemctl:return False
    try:
        subprocess.run([systemctl,'--user','daemon-reload'],check=True,capture_output=True,timeout=10)
        action='enable' if enable else 'disable'
        subprocess.run([systemctl,'--user',action,'--now',TIMER_NAME,LOGIN_TIMER_NAME],check=True,capture_output=True,timeout=10)
        if enable and changed:
            subprocess.run([systemctl,'--user','restart',TIMER_NAME,LOGIN_TIMER_NAME],check=True,capture_output=True,timeout=10)
        return True
    except (OSError,subprocess.SubprocessError):return False


def main():
    if '--enable-timer' in sys.argv:return 0 if install_user_timer(True) else 1
    if '--disable-timer' in sys.argv:return 0 if install_user_timer(False) else 1
    stage_update();return 0


if __name__=='__main__':raise SystemExit(main())
