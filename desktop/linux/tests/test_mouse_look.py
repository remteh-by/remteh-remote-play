import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mouse_look import settings,DEFAULTS
from session import preferences
from unittest.mock import patch

class MouseCameraOptions(unittest.TestCase):
    def test_corrupt_profile_is_bounded_and_strict_runtime_rejects_it(self):
        for key,value in [('mouse_raw_input',1),('mouse_smoothing_ms',math.nan),('mouse_smoothing_ms',17),('mouse_deadzone',True),('mouse_deadzone',.5),('mouse_response_curve',0)]:
            with self.subTest(key=key,value=value):
                self.assertEqual(settings({key:value}),DEFAULTS)
                with self.assertRaises(ValueError):settings({key:value},strict=True)
    def test_settings_survive_mac_preferences_without_resetting_bindings_or_speed(self):
        values=dict(mouse_raw_input=False,mouse_smoothing_ms=4,mouse_deadzone=.15,mouse_response_curve=1.8,mouse_sensitivity=.037)
        with patch('session.sys.platform','darwin'):
            saved=preferences(values)
            for key,value in values.items():self.assertEqual(saved[key],value)
            self.assertEqual(preferences(saved),saved)

    def test_editor_starfield_profile_is_optional_and_preserves_five_buttons(self):
        import test_launcher as fixture
        from macos_input_settings import InputSettingsDialog
        fixture.LauncherLifecycle.setUpClass()
        dialog=InputSettingsDialog({'mouse_sensitivity':.125},'ru')
        original=[combo.currentData() for combo in dialog.mouse_combos]
        dialog._starfield_profile();values=dialog.result_values()
        self.assertEqual(values['input_bindings']['mouse'],original)
        self.assertEqual(values['mouse_sensitivity'],.025)
        self.assertEqual(values['mouse_deadzone'],.12)
        self.assertEqual(values['mouse_response_curve'],1.6)
        dialog.close()
