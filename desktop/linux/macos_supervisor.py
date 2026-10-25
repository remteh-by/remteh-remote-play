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
from storage import PRIVATE,HERE


def main():
    os.umask(0o077)
    registration=json.loads((PRIVATE/'registration.json').read_text())
    from session import preferences as validated_preferences
    from macos_input_settings import encode_bindings
    preferences=validated_preferences(json.loads((PRIVATE/'preferences.json').read_text()))
    keyboard_bindings,mouse_bindings=encode_bindings(preferences.get('input_bindings'))
    with (PRIVATE/'stream.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return 73
        path=PRIVATE/'engine.sock'
        path.unlink(missing_ok=True)
        with socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM) as control:
            control.bind(str(path));path.chmod(0o600)
            from owned_macos_engine import prepare
            bridge=HERE/'assets/macos/libdeckivo-input.dylib'
            engine=prepare(ENGINE,bridge,PRIVATE,HERE/'assets/macos/libSDL2.dylib')
            if select.select([control],[],[],0)[0] and control.recv(32)==b'stop':return 0
            args=[str(engine),'--profile',PROFILE]
            if preferences.get('fullscreen',True):args+=['--fullscreen']
            args+=['stream',registration['server_nickname'],preferences['host']]
            env={**os.environ,'QSG_RHI_BACKEND':'opengl'}
            for key in ('LD_PRELOAD','LD_LIBRARY_PATH','QT_PLUGIN_PATH','QT_QPA_PLATFORM_PLUGIN_PATH','DYLD_LIBRARY_PATH','DYLD_FRAMEWORK_PATH'):
                env.pop(key,None)
            input_socket=PRIVATE/'input.sock'
            input_socket.unlink(missing_ok=True)
            stop_socket=PRIVATE/'adapter.sock';stop_socket.unlink(missing_ok=True)
            env.update(DYLD_INSERT_LIBRARIES=str(bridge),DECKIVO_INPUT_SOCKET=str(input_socket),DECKIVO_STOP_SOCKET=str(stop_socket),DECKIVO_METRICS=str(PRIVATE/'metrics.json'),DECKIVO_KBM='1' if preferences.get('keyboard_mouse',False) else '0',SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS='1',DECKIVO_MOUSE_SENSITIVITY=str(preferences.get('mouse_sensitivity',.025)),DECKIVO_MOUSE_INVERT_Y='1' if preferences.get('invert_mouse_y',False) else '0',DECKIVO_INPUT_LANG=str(preferences.get('language','en')))
            env.update(DECKIVO_KEY_BINDINGS=keyboard_bindings,DECKIVO_MOUSE_BINDINGS=mouse_bindings)
            child=subprocess.Popen(args,env=env)
            print('[Deckivo] engine_pid='+str(child.pid),flush=True)
            try:
                while child.poll() is None:
                    if select.select([control],[],[],.25)[0] and control.recv(32)==b'stop':
                        try:control.sendto(b'quit',str(stop_socket))
                        except OSError:quit_owned_engine(child.pid)
                return child.returncode
            finally:
                path.unlink(missing_ok=True);input_socket.unlink(missing_ok=True);stop_socket.unlink(missing_ok=True)


if __name__=='__main__':sys.exit(main())
