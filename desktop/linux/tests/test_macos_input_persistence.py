"""Persist settings in a temporary folder, then pass their wire form to real C.

No QApplication, owner preferences, controller device, or console is accessed.
The compiled harness includes the production input-state.h instead of duplicating
its parser or input sampling logic in Python.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
LINUX = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LINUX))

import session
from macos_input_settings import default_bindings, encode_bindings, normalize_bindings
from storage import private_json


HARNESS = r'''
#include "input-state.h"
#include <stdio.h>

static void sample(DkMacInput *state) {
    uint32_t buttons;
    int16_t axes[6];
    dk_mac_sample(state, 1.02, &buttons, axes);
    printf("[%u", (unsigned)buttons);
    for (unsigned i = 0; i < 6; i++) printf(",%d", (int)axes[i]);
    printf("]");
}

int main(int argc, char **argv) {
    if (argc != 5) return 2;
    DkMacInput state, defaults;
    dk_mac_init(&defaults, .025, false, 1.);
    dk_mac_init(&state, strtod(argv[3], NULL), strcmp(argv[4], "1") == 0, 1.);
    if (!dk_mac_bindings(&state, argv[1], false)) return 3;
    if (!dk_mac_bindings(&state, argv[2], true)) return 4;
    printf("{\"default_maps_equal\":%s,\"sensitivity\":%.17g,\"invert_y\":%s,\"keys\":[",
           memcmp(defaults.key_bindings, state.key_bindings, sizeof(state.key_bindings)) == 0 &&
           memcmp(defaults.mouse_bindings, state.mouse_bindings, sizeof(state.mouse_bindings)) == 0 ? "true" : "false",
           state.sensitivity, state.invert_y ? "true" : "false");
    for (unsigned key = 0; key < 128; key++) {
        if (key) printf(",");
        dk_mac_reset(&state, 1.);
        dk_mac_key(&state, key, true);
        sample(&state);
    }
    printf("],\"mouse\":[");
    for (unsigned button = 0; button < 5; button++) {
        if (button) printf(",");
        dk_mac_reset(&state, 1.);
        state.mouse[button] = true;
        sample(&state);
    }
    printf("],\"reset\":");
    dk_mac_reset(&state, 1.);
    sample(&state);
    printf("}\n");
    return 0;
}
'''


class MacInputPersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = shutil.which("clang") or shutil.which("cc")
        if not compiler:
            raise unittest.SkipTest("A C compiler is required for the actual native input core")
        cls.temporary = tempfile.TemporaryDirectory(prefix="deckivo-input-test-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        source = cls.root / "wire-input.c"
        source.write_text(HARNESS)
        cls.binary = cls.root / "wire-input"
        subprocess.run(
            [compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-O0",
             "-I", str(LINUX.parent / "macos"), str(source), "-lm", "-o", str(cls.binary)],
            check=True, capture_output=True, text=True, timeout=30,
        )

    @staticmethod
    def mac_preferences(value):
        # Exercise the macOS branch even when this isolated test runs on Linux CI.
        with patch.object(session.sys, "platform", "darwin"):
            return session.preferences(value)

    def persist(self, value):
        path = self.root / self._testMethodName / "private" / "preferences.json"
        normalized = self.mac_preferences(value)
        private_json(path, normalized)
        loaded = json.loads(path.read_text())
        result = self.mac_preferences(loaded)
        self.assertEqual(loaded, normalized)
        self.assertEqual(result, normalized)
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(path.parent.stat().st_mode & 0o777, 0o700)
        self.assertFalse(path.with_suffix(".json.tmp").exists())
        return result

    def native_result(self, preferences):
        keyboard, mouse = encode_bindings(preferences["input_bindings"])
        completed = subprocess.run(
            [str(self.binary), keyboard, mouse, str(preferences["mouse_sensitivity"]),
             "1" if preferences["invert_mouse_y"] else "0"],
            check=True, capture_output=True, text=True, timeout=5,
        )
        return json.loads(completed.stdout)

    def test_persisted_python_defaults_equal_native_defaults(self):
        saved = self.persist({"keyboard_mouse": True})
        self.assertEqual(saved["input_bindings"], default_bindings())
        native = self.native_result(saved)
        self.assertTrue(native["default_maps_equal"])
        self.assertEqual(native["keys"][13], [0, 0, -32767, 0, 0, -32768, -32768])
        self.assertEqual(native["mouse"][0], [0, 0, 0, 0, 0, -32768, 32767])
        self.assertEqual(native["mouse"][1], [0, 0, 0, 0, 0, 32767, -32768])
        self.assertEqual(native["mouse"][3][0], 1 << 1)
        self.assertEqual(native["mouse"][4][0], 1 << 2)

    def test_custom_json_round_trip_reaches_native_keys_and_side_buttons(self):
        custom = {"keyboard": {"6": 23, "7": 0, "62": 9, "60": 3,
                               "13": 20, "14": 22, "127": 30},
                  "mouse": [21, 22, 27, 20, 9]}
        saved = self.persist({"input_bindings": custom, "mouse_sensitivity": .02525,
                              "invert_mouse_y": True, "keyboard_mouse": True,
                              "host": "192.0.2.99", "quality": 4, "quality_schema": 2,
                              "history": False, "automatic_updates": False})
        self.assertEqual(saved["input_bindings"], normalize_bindings(custom))
        self.assertEqual(saved["mouse_sensitivity"], .02525)
        self.assertTrue(saved["keyboard_mouse"])
        self.assertEqual(saved["host"], "192.0.2.99")
        self.assertEqual(saved["quality"], 4)
        self.assertFalse(saved["history"])
        self.assertFalse(saved["automatic_updates"])
        native = self.native_result(saved)
        self.assertFalse(native["default_maps_equal"])
        self.assertEqual(native["sensitivity"], .02525)
        self.assertTrue(native["invert_y"])
        neutral = [0, 0, 0, 0, 0, -32768, -32768]
        self.assertEqual(native["keys"][6], [0, 0, -32767, 0, 0, -32768, -32768])
        self.assertEqual(native["keys"][7][0], 1)
        self.assertEqual(native["keys"][13][0], 1 << 20)  # W now means touchpad, not movement.
        self.assertEqual(native["keys"][14][6], 32767)  # A key can drive a trigger.
        self.assertEqual(native["keys"][127][3], 32767)
        self.assertEqual(native["keys"][59][0], 1 << 9)
        self.assertEqual(native["keys"][62], native["keys"][59])
        self.assertEqual(native["keys"][56][0], 1 << 3)
        self.assertEqual(native["keys"][60], native["keys"][56])
        self.assertEqual(native["keys"][49], neutral)  # Old Space binding was replaced.
        self.assertEqual(native["mouse"][0][5], 32767)
        self.assertEqual(native["mouse"][1][6], 32767)
        self.assertEqual(native["mouse"][2][4], -32767)
        self.assertEqual(native["mouse"][3][0], 1 << 20)
        self.assertEqual(native["mouse"][4][0], 1 << 9)
        self.assertEqual(native["reset"], neutral)

    def test_explicitly_unbound_inputs_stay_unbound_after_restart(self):
        saved = self.persist({"input_bindings": {"keyboard": {}, "mouse": [-1] * 5},
                              "keyboard_mouse": True})
        native = self.native_result(saved)
        neutral = [0, 0, 0, 0, 0, -32768, -32768]
        self.assertEqual(native["keys"], [neutral] * 128)
        self.assertEqual(native["mouse"], [neutral] * 5)
        self.assertEqual(native["reset"], neutral)


if __name__ == "__main__":
    unittest.main()
