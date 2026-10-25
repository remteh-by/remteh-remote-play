"""Read SDL controller state on macOS; never synthesize global input."""
import ctypes
from pathlib import Path
import time
from PyQt5.QtCore import QObject,QTimer,pyqtSignal


class ControllerMonitor(QObject):
    changed=pyqtSignal();navigate=pyqtSignal(str)
    def __init__(self,parent=None):
        super().__init__(parent);self.name='';self.axes={};self.buttons={};self.paused=False;self.pad=None;self.library=None;self.last_nav=0
        try:
            bundled=Path(__file__).resolve().parent/'assets/macos/libSDL2.dylib'
            lib=ctypes.CDLL(str(bundled) if bundled.is_file() else '/opt/homebrew/opt/sdl2/lib/libSDL2.dylib')
            lib.SDL_InitSubSystem.argtypes=[ctypes.c_uint32];lib.SDL_InitSubSystem(0x2200)
            lib.SDL_GameControllerOpen.argtypes=[ctypes.c_int];lib.SDL_GameControllerOpen.restype=ctypes.c_void_p
            lib.SDL_GameControllerName.argtypes=[ctypes.c_void_p];lib.SDL_GameControllerName.restype=ctypes.c_char_p
            lib.SDL_GameControllerGetButton.argtypes=[ctypes.c_void_p,ctypes.c_int];lib.SDL_GameControllerGetButton.restype=ctypes.c_uint8
            lib.SDL_GameControllerGetAxis.argtypes=[ctypes.c_void_p,ctypes.c_int];lib.SDL_GameControllerGetAxis.restype=ctypes.c_int16
            lib.SDL_GameControllerGetAttached.argtypes=[ctypes.c_void_p];lib.SDL_GameControllerClose.argtypes=[ctypes.c_void_p]
            self.library=lib
        except OSError:pass
        self.timer=QTimer(self);self.timer.timeout.connect(self.poll);self.timer.start(32)

    def suspend(self,value):self.paused=value;self.disconnect_device()
    def disconnect_device(self):
        if self.pad and self.library:self.library.SDL_GameControllerClose(self.pad)
        self.pad=None;self.name='';self.axes={};self.buttons={};self.changed.emit()
    def poll(self):
        if self.paused or not self.library:return
        lib=self.library;lib.SDL_GameControllerUpdate()
        if self.pad and not lib.SDL_GameControllerGetAttached(self.pad):self.disconnect_device()
        if not self.pad:
            for index in range(lib.SDL_NumJoysticks()):
                if lib.SDL_IsGameController(index):
                    self.pad=lib.SDL_GameControllerOpen(index)
                    if self.pad:self.name=(lib.SDL_GameControllerName(self.pad) or b'Gamepad').decode(errors='replace');break
        if not self.pad:return
        mapping={'south':0,'east':1,'west':2,'north':3,'select':4,'home':5,'start':6,'L3':7,'R3':8,'L1':9,'R1':10,'up':11,'down':12,'left':13,'right':14,'capture':15}
        new={key:bool(lib.SDL_GameControllerGetButton(self.pad,index)) for key,index in mapping.items()}
        for key,action in (('south','activate'),('east','back'),('L1','previous_page'),('R1','next_page')):
            if new[key] and not self.buttons.get(key):self.navigate.emit(action)
        self.buttons=new;self.axes={target:lib.SDL_GameControllerGetAxis(self.pad,index)/32767 for target,index in ((0,0),(1,1),(3,2),(4,3),(2,4),(5,5))}
        now=time.monotonic()
        if now-self.last_nav>.24:
            action=next((key for key in ('up','down','left','right') if new[key]),'')
            if not action:
                x,y=self.axes[0],self.axes[1];action='right' if x>.6 else 'left' if x<-.6 else 'down' if y>.6 else 'up' if y<-.6 else ''
            if action:self.navigate.emit(action);self.last_nav=now
        self.changed.emit()
