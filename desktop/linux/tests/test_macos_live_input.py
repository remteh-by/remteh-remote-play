"""Live input editing uses isolated widgets, files and an actual local socket."""
import json
from pathlib import Path
import socket
import sys
import unittest
from unittest.mock import Mock,patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import launcher,macos_main
from macos_input_settings import default_bindings
import test_launcher as launcher_fixture


class MacLiveInputTests(unittest.TestCase):
    def setUp(self):
        launcher_fixture.LauncherLifecycle.setUpClass()
        self.type_patch=patch.object(launcher,'Deckivo',macos_main.MacDeckivo);self.type_patch.start()
        self.case=launcher_fixture.LauncherLifecycle();self.case.setUp();self.window=self.case.window
        self.private=launcher.PRIVATE
        self.paths=[patch.object(macos_main,'PRIVATE',self.private),patch.object(macos_main,'CONFIG',launcher.CONFIG)]
        for item in self.paths:item.start()
        self.window.process=launcher_fixture.FakeProcess(self.window);self.window.process.running=True
        self.window.metrics={'pid':142};self.window.phase='connected';self.window.saw_video=True
        self.window.set_preferences_enabled(False)

    def tearDown(self):
        self.case.tearDown()
        for item in reversed(self.paths):item.stop()
        self.type_patch.stop()

    def test_mouse_keyboard_button_opens_editor_while_connection_is_locked(self):
        self.assertTrue(self.window.input_settings_button.isEnabled())
        self.assertFalse(self.window.host_edit.isEnabled())
        self.assertFalse(self.window.save_preferences_button.isEnabled())
        dialog=Mock();dialog.Accepted=1;dialog.exec_.return_value=1
        dialog.result_values.return_value={'input_bindings':default_bindings(),'mouse_sensitivity':.04,'invert_mouse_y':True}
        with patch('macos_input_settings.InputSettingsDialog',return_value=dialog) as editor,patch.object(self.window,'apply_live_input_settings') as apply:
            self.window.input_settings_button.click()
            editor.assert_called_once();apply.assert_called_once()
        stored=json.loads(launcher.CONFIG.read_text())
        self.assertEqual(stored['mouse_sensitivity'],.04)
        self.assertTrue(stored['invert_mouse_y']);self.assertTrue(stored['keyboard_mouse'])
        self.assertTrue(self.window.capture_button.isEnabled())

    def test_real_reload_request_needs_current_process_revision_and_controller_ack(self):
        self.window.preferences.update(input_bindings=default_bindings(),mouse_sensitivity=.035,invert_mouse_y=True,host='192.0.2.123')
        with socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM) as adapter:
            adapter.bind(str(self.private/'adapter.sock'));adapter.settimeout(1)
            with patch.object(macos_main.QTimer,'singleShot'):
                self.window.apply_live_input_settings()
            self.assertEqual(adapter.recv(16),b'conf')
        path=self.private/'input-runtime.json';request=json.loads(path.read_text())
        self.assertNotIn('host',request);self.assertEqual(path.stat().st_mode&0o777,0o600)
        self.assertEqual(request['sensitivity'],.035)
        revision=request['revision'];state=self.private/'metrics.json.input'
        state.write_text(json.dumps({'pid':143,'input_revision':revision,'controller_ready':True,'controller_open':True}))
        self.window.confirm_live_input_settings(revision,self.window.stream_id,0)
        self.assertEqual(self.window.settings_notice.text(),self.window.t('input_saved_next'))
        state.write_text(json.dumps({'pid':142,'input_revision':revision,'controller_ready':True,'controller_open':True}))
        self.window.confirm_live_input_settings(revision,self.window.stream_id,0)
        self.assertEqual(self.window.settings_notice.text(),self.window.t('input_applied'))

    def test_runtime_request_rejects_invalid_mouse_values_without_private_fields(self):
        values={'input_bindings':default_bindings(),'host':'192.0.2.123','mouse_sensitivity':.025,'invert_mouse_y':False}
        request=macos_main.runtime_input_request(values,'a'*32)
        self.assertEqual(set(request),{'schema','revision','keyboard','mouse','sensitivity','invert_y'})
        for speed in (True,float('nan'),0,1):
            with self.assertRaises(ValueError):macos_main.runtime_input_request({**values,'mouse_sensitivity':speed},'a'*32)
        with self.assertRaises(ValueError):macos_main.runtime_input_request(values,'bad revision')


if __name__=='__main__':unittest.main()
