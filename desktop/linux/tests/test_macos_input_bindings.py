"""Pure binding validation and offscreen UI checks; never access owner settings."""
import copy
import os
from pathlib import Path
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QApplication, QDialog, QPushButton

from macos_input_settings import (
    InputSettingsDialog, _KeyCaptureDialog, default_bindings, encode_bindings,
    normalize_bindings,
)


class BindingValidationTests(unittest.TestCase):
    def test_defaults_and_detached_result(self):
        defaults = default_bindings()
        self.assertEqual(defaults["mouse"], [22, 21, 8, 1, 2])
        self.assertEqual([defaults["keyboard"][code] for code in ["13", "1", "0", "2"]], [23, 24, 25, 26])
        self.assertEqual(normalize_bindings(None), defaults)
        self.assertEqual(normalize_bindings([]), defaults)
        result = normalize_bindings(defaults)
        result["keyboard"].clear()
        result["mouse"][0] = -1
        self.assertEqual(defaults, default_bindings())

    def test_empty_is_distinct_from_missing(self):
        self.assertEqual(normalize_bindings({"keyboard": {}})["keyboard"], {})
        self.assertEqual(normalize_bindings({"keyboard": []})["keyboard"], default_bindings()["keyboard"])
        self.assertEqual(encode_bindings({"keyboard": {}, "mouse": [-1] * 5}), ("", "0:-1,1:-1,2:-1,3:-1,4:-1"))

    def test_only_valid_keys_and_integer_actions(self):
        sample = {"keyboard": {"13": 23, "0": -1, "8": True, True: 3,
                              "2": "26", "3": 1.0, "127": 30, "128": 0,
                              "-1": 0, "bad": 0, "2.0": 1, "5": 123,
                              "１２": 2, "53": 0, "100": 2, "103": 3,
                              "54": 4, "55": 5, "57": 6, "63": 7}}
        self.assertEqual(normalize_bindings(sample)["keyboard"], {"13": 23, "127": 30})

    def test_canonical_modifiers_win_independent_of_insertion_order(self):
        entries = [("60", 3), ("61", 2), ("62", 1), ("56", 7), ("58", 8), ("59", 9)]
        expected = {"56": 7, "58": 8, "59": 9}
        self.assertEqual(normalize_bindings({"keyboard": dict(entries)})["keyboard"], expected)
        self.assertEqual(normalize_bindings({"keyboard": dict(reversed(entries))})["keyboard"], expected)
        self.assertEqual(normalize_bindings({"keyboard": {"60": 7, "61": 8, "62": 1}})["keyboard"], {"56": 7, "58": 8, "59": 1})

    def test_two_keys_per_action_and_idempotence(self):
        data = {"keyboard": {"20": 0, "3": 0, "0": 0, "60": 7}, "mouse": [0, -1, 21, 22, 30]}
        normal = normalize_bindings(data)
        self.assertEqual(normal["keyboard"], {"0": 0, "3": 0, "56": 7})
        self.assertEqual(normalize_bindings(normal), normal)

    def test_invalid_mouse_items_fall_back_individually(self):
        self.assertEqual(normalize_bindings({"mouse": [-1, True, 30, "21", 100]})["mouse"], [-1, 21, 30, 1, 2])
        for invalid in [[], [0, 1], "0,1,2,3,4", None]:
            self.assertEqual(normalize_bindings({"mouse": invalid})["mouse"], [22, 21, 8, 1, 2])

    def test_native_encoding_is_numeric_and_deterministic(self):
        self.assertEqual(encode_bindings({"keyboard": {"120": 5, "13": 23, "0": 25}, "mouse": [22, 21, 8, -1, 30]}),
                         ("0:25,13:23,120:5", "0:22,1:21,2:8,3:-1,4:30"))
        self.assertEqual(encode_bindings({"keyboard": {"0;rm": 0, "9": 123}})[0], "")


class BindingDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.dialogs = []

    def tearDown(self):
        for dialog in self.dialogs:
            dialog.close()
            dialog.deleteLater()
        self.app.processEvents()

    def make_dialog(self, preferences=None, language="en"):
        dialog = InputSettingsDialog(preferences or {}, language)
        self.dialogs.append(dialog)
        return dialog

    def test_two_tabs_five_buttons_and_default_speed(self):
        dialog = self.make_dialog()
        dialog.show()
        self.app.processEvents()
        self.assertEqual(dialog.tabs.count(), 2)
        self.assertEqual(len(dialog.mouse_combos), 5)
        self.assertEqual(dialog.speed_spin.value(), 100)
        self.assertEqual(dialog.result_values(), {"input_bindings": normalize_bindings(None), "mouse_sensitivity": 0.025, "invert_mouse_y": False, "keyboard_mouse": True})

    def test_assignment_moves_duplicate_and_clear_works(self):
        dialog = self.make_dialog()
        dialog._assign_key(0, 0, 13)  # Move W from walking to Cross, replacing Space.
        mapping = dialog.result_values()["input_bindings"]["keyboard"]
        self.assertEqual(mapping["13"], 0)
        self.assertNotIn("49", mapping)
        self.assertEqual(dialog._keys_for_action(23), [])
        self.assertIn("moved", dialog.status.text())
        dialog._clear_key(0, 0)
        self.assertNotIn("13", dialog.result_values()["input_bindings"]["keyboard"])

    def test_both_side_buttons_speed_and_cancel_leave_source_unchanged(self):
        prefs = {"input_bindings": default_bindings(), "mouse_sensitivity": 0.025, "invert_mouse_y": False}
        original = copy.deepcopy(prefs)
        dialog = self.make_dialog(prefs, "ru")
        dialog.mouse_combos[3].setCurrentIndex(dialog.mouse_combos[3].findData(20))
        dialog.mouse_combos[4].setCurrentIndex(dialog.mouse_combos[4].findData(-1))
        dialog.speed_slider.setValue(240)
        dialog.invert_check.setChecked(True)
        result = dialog.result_values()
        self.assertEqual(result["input_bindings"]["mouse"][3:], [20, -1])
        self.assertAlmostEqual(result["mouse_sensitivity"], 0.06)
        self.assertTrue(result["invert_mouse_y"])
        dialog.reject()
        self.assertEqual(prefs, original)

    def test_restore_and_sensitivity_validation(self):
        for raw in [None, True, "nonsense", float("nan"), float("inf")]:
            self.assertEqual(self.make_dialog({"mouse_sensitivity": raw}).speed_spin.value(), 100)
        dialog = self.make_dialog({"mouse_sensitivity": 500, "invert_mouse_y": True, "input_bindings": {"keyboard": {}, "mouse": [-1] * 5}})
        self.assertEqual(dialog.speed_spin.value(), 800)
        self.assertAlmostEqual(dialog.result_values()["mouse_sensitivity"], 0.2)
        dialog.speed_spin.setValue(4)
        self.assertEqual(dialog.speed_slider.value(), 4)
        self.assertAlmostEqual(dialog.result_values()["mouse_sensitivity"], 0.001)
        dialog._restore_defaults()
        self.assertEqual(dialog.result_values()["input_bindings"], normalize_bindings(None))
        self.assertFalse(dialog.invert_check.isChecked())
        self.assertEqual(dialog.speed_spin.value(), 100)

    def capture_event(self, code, qt_key, text="", focused_button=False):
        capture = _KeyCaptureDialog(lambda en, ru: en)
        self.dialogs.append(capture)
        capture.show()
        self.app.processEvents()
        target = capture.findChild(QPushButton) if focused_button else capture
        event = QKeyEvent(QEvent.KeyPress, qt_key, Qt.NoModifier, 0, code, 0, text)
        self.app.sendEvent(target, event)
        return capture

    def test_capture_uses_physical_key_in_both_layouts_including_zero(self):
        for text in ["w", "ц"]:
            capture = self.capture_event(13, Qt.Key_W, text)
            self.assertEqual(capture.key_code, 13)
            self.assertEqual(capture.result(), QDialog.Accepted)
        self.assertEqual(self.capture_event(0, Qt.Key_A, "ф").key_code, 0)
        for code, qt_key, canonical in [(56, Qt.Key_Shift, 56), (60, Qt.Key_Shift, 56),
                                        (58, Qt.Key_Alt, 58), (61, Qt.Key_Alt, 58),
                                        (59, Qt.Key_Control, 59), (62, Qt.Key_Control, 59)]:
            self.assertEqual(self.capture_event(code, qt_key, focused_button=True).key_code, canonical)

    def test_tab_space_capture_on_focused_cancel_button(self):
        for code, qt_key in [(48, Qt.Key_Tab), (49, Qt.Key_Space)]:
            capture = self.capture_event(code, qt_key, focused_button=True)
            self.assertEqual(capture.key_code, code)
            self.assertEqual(capture.result(), QDialog.Accepted)

    def test_reserved_keys_rejected_and_escape_cancels(self):
        for code, qt_key in [(100, Qt.Key_F8), (103, Qt.Key_F11), (55, Qt.Key_Meta)]:
            capture = self.capture_event(code, qt_key)
            self.assertIsNone(capture.key_code)
            self.assertIn("reserved", capture.hint.text())
            self.assertTrue(capture.isVisible())
        escape = self.capture_event(53, Qt.Key_Escape)
        self.assertEqual(escape.result(), QDialog.Rejected)
        self.assertIsNone(escape.key_code)


if __name__ == "__main__":
    unittest.main()
