"""Regression cases from the 29 October audit; no real console or input device."""
import http.client,json,os,plistlib,sys,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import controller_lab,i18n,keyboard_mouse,linux_input_settings,macos_engine
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtCore import QEvent

class TranslationTests(unittest.TestCase):
    def test_every_advertised_language_has_real_dashboard_and_same_keys(self):
        catalogs=i18n.catalogs()
        for lang in i18n.LANGUAGES:
            self.assertEqual(set(catalogs['en']),set(catalogs[lang]))
            self.assertTrue(all(v.strip() for v in catalogs[lang].values()))
            if lang!='en':self.assertNotEqual(i18n.text('home',lang),i18n.text('home','en'))
    def test_auto_and_explicit_choices(self):
        for choice,system,wanted in [('auto','ru_RU','ru'),('auto','ar_SA','ar'),('auto','zh-Hant','zh'),('de','ru_RU','de'),('auto','fi_FI','en')]:
            self.assertEqual(i18n.effective_language(choice,system),wanted)

class InputTests(unittest.TestCase):
    def test_all_five_buttons_and_keyboard_use_saved_actions(self):
        bindings={'keyboard':{'17':0},'mouse':[0,1,2,3,20]}
        state=keyboard_mouse.InputState(bindings=bindings)
        import struct
        for i,name in enumerate(('left','right','middle','side1','side2')):
            state.reset();state.mouse_buttons.add(name)
            self.assertEqual(struct.unpack('<4sII6h',state.packet())[2],1<<bindings['mouse'][i])
        state.reset();self.assertTrue(state.key('17',True))
        self.assertEqual(struct.unpack('<4sII6h',state.packet())[2],1)
        state.reset();self.assertEqual(struct.unpack('<4sII6h',state.packet())[2],0)
    def test_ru_and_en_physical_positions_and_unknown_keys(self):
        for char in ('w','ц'):
            event=QKeyEvent(QEvent.KeyPress,Qt.Key_W,Qt.NoModifier,char)
            self.assertEqual(linux_input_settings.capture_code(event),17)
        unknown=QKeyEvent(QEvent.KeyPress,Qt.Key_unknown,Qt.NoModifier,'')
        self.assertIsNone(linux_input_settings.capture_code(unknown))
    def test_reserved_keys_and_invalid_saved_bindings(self):
        b=linux_input_settings.normalize_bindings({'keyboard':{'1':0,'17':False,'999':0,'30':25},'mouse':[22,21,8,True,999]})
        self.assertEqual(b['keyboard'],{'30':25});self.assertEqual(b['mouse'],[22,21,8,1,2])
    def test_editor_round_trip_and_side_button_events(self):
        from PyQt5.QtWidgets import QApplication
        from macos_input_settings import InputSettingsDialog
        from input_overlay import KeyboardMouseOverlay
        app=QApplication.instance() or QApplication([])
        dialog=InputSettingsDialog({},'de',platform='linux')
        dialog._assign_key(20,0,17)
        dialog.mouse_combos[3].setCurrentIndex(dialog.mouse_combos[3].findData(21))
        result=dialog.result_values();self.assertEqual(result['linux_input_bindings']['keyboard']['17'],20)
        self.assertEqual(result['linux_input_bindings']['mouse'][3],21)
        owner=SimpleNamespace(state=keyboard_mouse.InputState(bindings=result['linux_input_bindings']),transmit=Mock())
        for button,key in ((Qt.XButton1,'side1'),(Qt.XButton2,'side2')):
            event=SimpleNamespace(button=lambda:button)
            KeyboardMouseOverlay.mousePressEvent(owner,event);self.assertIn(key,owner.state.mouse_buttons)
            KeyboardMouseOverlay.mouseReleaseEvent(owner,event);self.assertNotIn(key,owner.state.mouse_buttons)
        dialog.close();app.processEvents()

class EngineTests(unittest.TestCase):
    def bundle(self,root,version='1.10.0',identifier='org.streetpea.chiaking'):
        app=root/'Space in name/chiaki-ng.app';binary=app/'Contents/MacOS/chiaki';binary.parent.mkdir(parents=True)
        binary.write_bytes(b'test Mach-O');binary.chmod(0o700)
        (app/'Contents/Info.plist').write_bytes(plistlib.dumps({'CFBundleIdentifier':identifier,'CFBundleExecutable':'chiaki','CFBundleShortVersionString':version}))
        return binary
    def test_user_path_spaces_and_architecture_validation(self):
        with tempfile.TemporaryDirectory() as d:
            binary=self.bundle(Path(d))
            with patch.object(macos_engine.subprocess,'run',return_value=SimpleNamespace(stdout='arm64 x86_64')):
                self.assertEqual(macos_engine.resolve_engine({'engine_path':str(binary.parents[2])}),binary.resolve())
            binary.write_bytes(b'changed')
            with patch.object(macos_engine.subprocess,'run',return_value=SimpleNamespace(stdout='x86_64')):
                self.assertIsNone(macos_engine.inspect_engine(binary))
    def test_unknown_bundle_never_runs_and_invalid_choice_does_not_fall_back(self):
        with tempfile.TemporaryDirectory() as d:
            binary=self.bundle(Path(d),identifier='foreign.app')
            with patch.object(macos_engine.subprocess,'run') as run:
                self.assertIsNone(macos_engine.resolve_engine({'engine_path':str(binary)}));run.assert_not_called()

class BrowserOwnershipTests(unittest.TestCase):
    def setUp(self):
        original=controller_lab.LocalServer
        with patch.object(controller_lab,'LocalServer',side_effect=lambda address,handler:original(('127.0.0.1',0),handler)):
            self.lab=controller_lab.ControllerLab()
        self.lab.started=time.monotonic();self.lab.browser=SimpleNamespace(poll=lambda:0)
    def tearDown(self):self.lab.close()
    def test_real_page_close_message_and_profile_handoff(self):
        client=http.client.HTTPConnection('127.0.0.1',self.lab.server.server_port,timeout=2)
        for kind in ('open','close'):
            client.request('POST','/desktop-presence',json.dumps({'id':'page','token':self.lab.token,'kind':kind}),{'Content-Type':'text/plain'})
            response=client.getresponse();self.assertEqual(response.status,204);response.read()
        client.close()
        with patch.object(controller_lab.time,'monotonic',return_value=time.monotonic()+2):self.assertTrue(self.lab.finished())
    def test_hidden_live_browser_is_not_reclaimed_on_heartbeat_age(self):
        self.lab.presence('page','open')
        with patch.object(self.lab,'browser_alive',return_value=True),patch.object(controller_lab.time,'monotonic',return_value=time.monotonic()+3600):
            self.assertFalse(self.lab.finished())
    def test_dead_browser_and_untrusted_messages(self):
        self.lab.presence('page','open')
        with patch.object(self.lab,'browser_alive',return_value=False),patch.object(controller_lab.time,'monotonic',return_value=time.monotonic()+11):self.assertTrue(self.lab.finished())
        client=http.client.HTTPConnection('127.0.0.1',self.lab.server.server_port,timeout=2)
        client.request('POST','/desktop-presence',json.dumps({'id':'page','token':'wrong','kind':'close'}))
        response=client.getresponse();self.assertEqual(response.status,400);response.read();client.close()

class DashboardLabTests(unittest.TestCase):
    def setUp(self):
        from test_launcher import LauncherLifecycle
        LauncherLifecycle.setUpClass();self.case=LauncherLifecycle();self.case.setUp();self.window=self.case.window
    def tearDown(self):self.case.tearDown()
    def test_launch_error_restores_monitor(self):
        fake=Mock();fake.open.side_effect=RuntimeError('no browser')
        with patch.object(controller_lab,'ControllerLab',return_value=fake),patch('launcher.QMessageBox.warning'):
            self.window.open_controller_lab()
        self.assertFalse(self.window.pad.paused);self.assertIsNone(self.window.controller_lab)
    def test_separate_close_restores_monitor_and_auto_locale(self):
        fake=Mock();fake.finished.return_value=False
        self.window.language='auto'
        with patch('launcher.QLocale.system',return_value=SimpleNamespace(name=lambda:'ru_RU')),patch.object(controller_lab,'ControllerLab',return_value=fake):
            self.window.open_controller_lab();fake.open.assert_called_once_with('ru')
        self.assertTrue(self.window.pad.paused)
        fake.finished.return_value=True;self.window.poll_controller_lab()
        self.assertFalse(self.window.pad.paused);self.assertIsNone(self.window.controller_lab)
