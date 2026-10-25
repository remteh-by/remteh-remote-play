"""Keep the single-stream lock until the native macOS engine has exited."""
import fcntl
import json
import os
from pathlib import Path
import select
import socket
import subprocess
import sys
from macos_engine import ENGINE,PROFILE,quit_owned_engine
from storage import PRIVATE


def main():
    os.umask(0o077)
    registration=json.loads((PRIVATE/'registration.json').read_text())
    preferences=json.loads((PRIVATE/'preferences.json').read_text())
    with (PRIVATE/'stream.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return 73
        path=PRIVATE/'engine.sock'
        path.unlink(missing_ok=True)
        with socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM) as control:
            control.bind(str(path));path.chmod(0o600)
            args=[str(ENGINE),'--profile',PROFILE]
            if preferences.get('fullscreen',True):args+=['--fullscreen']
            args+=['stream',registration['server_nickname'],preferences['host']]
            env={**os.environ,'QSG_RHI_BACKEND':'opengl'}
            for key in ('LD_PRELOAD','LD_LIBRARY_PATH','QT_PLUGIN_PATH','QT_QPA_PLATFORM_PLUGIN_PATH','DYLD_LIBRARY_PATH','DYLD_FRAMEWORK_PATH'):
                env.pop(key,None)
            child=subprocess.Popen(args,env=env)
            print('[Deckivo] engine_pid='+str(child.pid),flush=True)
            try:
                while child.poll() is None:
                    if select.select([control],[],[],.25)[0] and control.recv(32)==b'stop':
                        quit_owned_engine(child.pid)
                return child.returncode
            finally:path.unlink(missing_ok=True)


if __name__=='__main__':sys.exit(main())
