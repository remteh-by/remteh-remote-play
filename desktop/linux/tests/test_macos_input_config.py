"""Verify private engine input ownership without reading/writing owner settings."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from PyQt5.QtCore import QSettings

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


if __name__ == '__main__':
    unittest.main()
