"""Verify private engine input ownership without reading/writing owner settings."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from PyQt5.QtCore import QSettings,QRect

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import macos_engine


class MacInputConfigurationTests(unittest.TestCase):
    def test_owned_profile_disables_both_stock_input_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder)/'isolated-test.ini')
            seed = QSettings(path, QSettings.IniFormat)
            seed.setValue('settings/keyboard_enabled', True)
            seed.setValue('settings/mouse_touch_enabled', True)
            seed.setValue('settings/enable_dualsense', True)
            seed.sync()

            def isolated_settings(organization, application):
                self.assertEqual((organization, application), ('Chiaki', 'Chiaki-Deckivo'))
                return QSettings(path, QSettings.IniFormat)

            with patch.object(macos_engine, 'QSettings', side_effect=isolated_settings) as factory:
                macos_engine.configure({'server_nickname': 'Local test fixture'}, 0)

            factory.assert_called_once_with('Chiaki', 'Chiaki-Deckivo')
            stored = QSettings(path, QSettings.IniFormat)
            self.assertFalse(stored.value('settings/keyboard_enabled', True, type=bool))
            self.assertFalse(stored.value('settings/mouse_touch_enabled', True, type=bool))
            self.assertTrue(stored.value('settings/enable_dualsense', False, type=bool))
            self.assertEqual(stored.value('settings/disconnect_action'), 'nothing')
            self.assertEqual(Path(path).stat().st_mode & 0o777, 0o600)

    def test_video_pixels_do_not_restore_an_oversized_retina_window(self):
        with tempfile.TemporaryDirectory() as folder:
            path=str(Path(folder)/'engine.ini');seed=QSettings(path,QSettings.IniFormat)
            seed.setValue('settings/geometry',QRect(0,0,1920,1080))
            seed.setValue('settings/stream_geometry',QRect(0,0,1920,1080));seed.sync()
            with patch.object(macos_engine,'QSettings',lambda *args:QSettings(path,QSettings.IniFormat)):
                macos_engine.configure({'server_nickname':'Isolated fixture'},3,QRect(0,0,1470,923))
            stored=QSettings(path,QSettings.IniFormat)
            self.assertFalse(stored.contains('settings/geometry'))
            self.assertFalse(stored.contains('settings/stream_geometry'))
            self.assertEqual(stored.value('settings/window_type'),'Adjust Manually')
            self.assertEqual(stored.value('settings/resolution_local_ps5'),'1080p')


if __name__ == '__main__':
    unittest.main()
