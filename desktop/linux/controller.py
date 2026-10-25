"""Read only Linux joydev monitor for the launcher and controller lab.

The engine owns exclusive evdev capture during a stream. This monitor is closed
before the engine starts; it never grabs an input device or synthesizes OS keys.
"""
import array
import fcntl
import os
from pathlib import Path
import struct
import time

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

BUTTONS = {304: 'south', 305: 'east', 307: 'north', 308: 'west',
           310: 'L1', 311: 'R1', 312: 'L2', 313: 'R2', 314: 'select',
           315: 'start', 316: 'home', 317: 'L3', 318: 'R3',
           544: 'up', 545: 'down', 546: 'left', 547: 'right', 704: 'capture'}


class ControllerMonitor(QObject):
    changed = pyqtSignal()
    navigate = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.fd = None
        self.path = ''
        self.name = ''
        self.buttons = {}
        self.axes = {}
        self.button_map = []
        self.axis_map = []
        self.paused = False
        self.last_scan = 0
        self.last_navigation = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll)
        self.timer.start(32)

    def suspend(self, value):
        self.paused = value
        self.disconnect_device()

    def disconnect_device(self):
        if self.fd is not None:
            os.close(self.fd)
        self.fd = None
        self.name = ''
        self.buttons = {}
        self.axes = {}
        self.changed.emit()

    def open_device(self):
        for path in sorted(Path('/dev/input').glob('js*')):
            try:
                fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
                name = bytearray(128)
                fcntl.ioctl(fd, 0x80806a13, name)  # JSIOCGNAME(128)
                decoded = name.split(b'\0')[0].decode(errors='replace')
                if 'joy-con' in decoded.lower():
                    os.close(fd)
                    continue
                axes = array.array('B', [0] * 64)
                buttons = array.array('H', [0] * 512)
                fcntl.ioctl(fd, 0x80406a32, axes)   # JSIOCGAXMAP
                fcntl.ioctl(fd, 0x84006a34, buttons)  # JSIOCGBTNMAP
                self.fd, self.path, self.name = fd, str(path), decoded
                self.axis_map, self.button_map = list(axes), list(buttons)
                self.changed.emit()
                return
            except OSError:
                if 'fd' in locals():
                    try:
                        os.close(fd)
                    except OSError:
                        pass

    def poll(self):
        if self.paused:
            return
        now = time.monotonic()
        if self.fd is None:
            if now - self.last_scan > 2:
                self.last_scan = now
                self.open_device()
            return
        changed = False
        try:
            for _ in range(128):
                try:
                    raw = os.read(self.fd, 8)
                except BlockingIOError:
                    break
                if len(raw) != 8:
                    self.disconnect_device()
                    return
                _, value, kind, number = struct.unpack('IhBB', raw)
                initial, kind = bool(kind & 0x80), kind & 0x7f
                if kind == 1 and number < len(self.button_map):
                    name = BUTTONS.get(self.button_map[number], f'button{number}')
                    self.buttons[name] = bool(value)
                    if value and not initial:
                        action = {'south': 'activate', 'east': 'back',
                                  'L1': 'previous_page', 'R1': 'next_page'}.get(name, name)
                        if action in ('activate', 'back', 'previous_page', 'next_page',
                                      'up', 'down', 'left', 'right'):
                            self.navigate.emit(action)
                elif kind == 2 and number < len(self.axis_map):
                    self.axes[self.axis_map[number]] = value / 32767.0
                changed = True
        except OSError:
            self.disconnect_device()
            return
        if now - self.last_navigation > .24:
            x = self.axes.get(16, 0) or self.axes.get(0, 0)
            y = self.axes.get(17, 0) or self.axes.get(1, 0)
            action = 'right' if x > .6 else 'left' if x < -.6 else 'down' if y > .6 else 'up' if y < -.6 else ''
            if action:
                self.navigate.emit(action)
                self.last_navigation = now
        if changed:
            self.changed.emit()
