"""Keep the single-stream lock until the native macOS engine has exited."""
import fcntl
import json
import os
from pathlib import Path
import select
import socket
import subprocess
import sys
import time
from macos_engine import resolve_engine,PROFILE,quit_owned_engine
from storage import PRIVATE,HERE


def supervise_engine(child, control, adapter_socket, grace_seconds=3.0, terminate_seconds=1.0):
    """Give an explicitly closed stream bounded time to leave the native engine.

    A stuck Qt destructor can keep joining a live session after its window has
    closed. Escalate only after the owner requested stop or the owned window
    reported closing; never kill a healthy session because it has no video.
    Repeated stop messages must not extend the deadline.
    """
    deadline=None
    while child.poll() is None:
        if select.select([control],[],[],.1)[0]:
            command=control.recv(32)
            if command in (b'stop',b'closing') and deadline is None:
                deadline=time.monotonic()+grace_seconds
                if command==b'stop':
                    try:control.sendto(b'quit',str(adapter_socket))
                    except OSError:
                        try:quit_owned_engine(child.pid)
                        except (OSError,AttributeError):
                            print('[Deckivo] native quit request unavailable; waiting for stop deadline',flush=True)
        if deadline is not None and time.monotonic()>=deadline:
            print('[Deckivo] native close timed out; terminating owned stream client',flush=True)
            try:child.terminate()
            except ProcessLookupError:pass
            try:child.wait(timeout=terminate_seconds)
            except subprocess.TimeoutExpired:
                print('[Deckivo] native close still blocked; killing owned stream client',flush=True)
                try:child.kill()
                except ProcessLookupError:pass
                # Keep the stream lock until the exact child has been reaped.
                child.wait()
    return child.returncode


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
            source=resolve_engine(preferences)
            if source is None:raise RuntimeError('Compatible chiaki-ng engine not found')
            engine=prepare(source,bridge,PRIVATE,HERE/'assets/macos/libSDL2.dylib')
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
            env.update(DYLD_INSERT_LIBRARIES=str(bridge),DECKIVO_INPUT_SOCKET=str(input_socket),DECKIVO_STOP_SOCKET=str(stop_socket),DECKIVO_SUPERVISOR_SOCKET=str(path),DECKIVO_METRICS=str(PRIVATE/'metrics.json'),DECKIVO_KBM='1' if preferences.get('keyboard_mouse',False) else '0',SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS='1',DECKIVO_MOUSE_SENSITIVITY=str(preferences.get('mouse_sensitivity',.025)),DECKIVO_MOUSE_INVERT_Y='1' if preferences.get('invert_mouse_y',False) else '0',DECKIVO_INPUT_LANG=str(preferences.get('language','en')))
            env.update(DECKIVO_KEY_BINDINGS=keyboard_bindings,DECKIVO_MOUSE_BINDINGS=mouse_bindings)
            child=subprocess.Popen(args,env=env)
            print('[Deckivo] engine_pid='+str(child.pid),flush=True)
            try:
                return supervise_engine(child,control,stop_socket)
            finally:
                path.unlink(missing_ok=True);input_socket.unlink(missing_ok=True);stop_socket.unlink(missing_ok=True)


if __name__=='__main__':sys.exit(main())
