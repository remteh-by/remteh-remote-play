"""Exercise SDL polling with a fake pad; never open the owner's controller."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from PyQt5.QtCore import QCoreApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import controller_macos


class Function:
    def __init__(self, call):
        self.call = call

    def __call__(self, *args):
        return self.call(*args)


class FakeSDL:
    def __init__(self):
        self.connected = True
        self.buttons = set()
        self.axes = {}
        functions = {
            'SDL_InitSubSystem': lambda flags: 0,
            'SDL_GameControllerUpdate': lambda: None,
            'SDL_NumJoysticks': lambda: int(self.connected),
            'SDL_IsGameController': lambda index: self.connected,
            'SDL_GameControllerOpen': lambda index: 1 if self.connected else None,
            'SDL_GameControllerClose': lambda pad: None,
            'SDL_GameControllerGetAttached': lambda pad: self.connected,
            'SDL_GameControllerName': lambda pad: b'Isolated test pad',
            'SDL_GameControllerGetButton': lambda pad, button: button in self.buttons,
            'SDL_GameControllerGetAxis': lambda pad, axis: self.axes.get(axis, 0),
        }
        for name, call in functions.items():
            setattr(self, name, Function(call))


class ControllerNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.sdl = FakeSDL()
        with patch.object(controller_macos.ctypes, 'CDLL', return_value=self.sdl):
            self.monitor = controller_macos.ControllerMonitor()
        self.monitor.timer.stop()
        self.actions = []
        self.monitor.navigate.connect(self.actions.append)

    def tearDown(self):
        self.monitor.disconnect_device()
        self.monitor.deleteLater()

    def test_face_and_shoulder_buttons_require_release_after_connect_and_resume(self):
        self.sdl.buttons = {0, 1, 9, 10}
        self.monitor.poll()
        self.monitor.poll()
        self.assertEqual(self.actions, [])
        self.assertTrue(self.monitor.buttons['south'])  # Live state remains truthful.
        self.sdl.buttons.clear()
        self.monitor.poll()
        self.sdl.buttons = {0, 1, 9, 10}
        self.monitor.poll()
        self.assertEqual(self.actions, ['activate', 'back', 'previous_page', 'next_page'])
        self.actions.clear()
        self.monitor.suspend(True)
        self.monitor.suspend(False)
        self.monitor.poll()
        self.assertEqual(self.actions, [])

    def test_replacement_pad_cannot_confirm_with_a_button_already_held(self):
        self.monitor.poll()
        self.sdl.connected = False
        self.monitor.poll()
        self.sdl.connected = True
        self.sdl.buttons = {0}
        self.monitor.poll()
        self.monitor.poll()
        self.assertEqual(self.actions, [])
        self.sdl.buttons.clear()
        self.monitor.poll()
        self.sdl.buttons = {0}
        self.monitor.poll()
        self.assertEqual(self.actions, ['activate'])

    def test_direction_requires_neutral_after_resume_then_repeats_normally(self):
        self.sdl.axes[0] = 30000
        self.monitor.poll()
        self.monitor.last_nav = 0
        self.monitor.poll()
        self.assertEqual(self.actions, [])
        self.sdl.axes.clear()
        self.monitor.poll()
        self.sdl.buttons = {14}
        self.monitor.poll()
        self.monitor.last_nav = 0
        self.monitor.poll()
        self.assertEqual(self.actions, ['right', 'right'])


if __name__ == '__main__':
    unittest.main()
