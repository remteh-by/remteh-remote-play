import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import update_background


class BackgroundUpdateTests(unittest.TestCase):
    def paths(self,root):
        return [patch.object(update_background,'PRIVATE',root),patch.object(update_background,'CACHE',root/'updates'),
            patch.object(update_background,'PENDING',root/'updates/pending.json'),
            patch.object(update_background,'STATUS',root/'status.json'),
            patch.object(update_background,'CONFIG',root/'preferences.json')]

    def test_disabled_preference_does_not_contact_update_channel(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);root.joinpath('preferences.json').write_text(json.dumps({'automatic_updates':False}))
            patches=self.paths(root)
            for item in patches:item.start()
            try:
                with patch.object(update_background,'check_and_download') as check:
                    self.assertIsNone(update_background.stage_update());check.assert_not_called()
                self.assertEqual(json.loads((root/'status.json').read_text())['state'],'disabled')
            finally:
                for item in reversed(patches):item.stop()

    def test_closed_app_stages_descriptor_without_launching_ui(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);ready={'entry':{'version':'0.8.2','build':18},'file':'package','index':'index','signature':'sig'}
            patches=self.paths(root)
            for item in patches:item.start()
            try:
                with patch.object(update_background,'application_running',return_value=False),\
                     patch.object(update_background,'check_and_download',return_value=ready) as check:
                    self.assertEqual(update_background.stage_update(),ready);check.assert_called_once()
                self.assertEqual(json.loads((root/'updates/pending.json').read_text()),ready)
                self.assertEqual(json.loads((root/'status.json').read_text())['state'],'ready')
            finally:
                for item in reversed(patches):item.stop()

    def test_valid_pending_update_does_not_repeat_network_download(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);ready={'entry':{'version':'0.8.2','build':18}}
            root.joinpath('updates').mkdir();root.joinpath('updates/pending.json').write_text(json.dumps(ready))
            patches=self.paths(root)
            for item in patches:item.start()
            try:
                with patch.object(update_background,'application_running',return_value=False),\
                     patch.object(update_background,'validate_staged',return_value=ready),\
                     patch.object(update_background,'check_and_download') as check:
                    self.assertEqual(update_background.stage_update(),ready);check.assert_not_called()
            finally:
                for item in reversed(patches):item.stop()

    def test_user_timer_has_bounded_cadence_and_no_ui_launch(self):
        service,timer,login_timer=update_background.unit_text()
        self.assertIn('update_background.py --check',service)
        self.assertNotIn('/.local/bin/deckivo',service)
        self.assertIn('OnStartupSec=45s',login_timer)
        self.assertIn('RandomizedDelaySec=0',login_timer)
        self.assertIn('OnUnitInactiveSec=60min',timer)
        self.assertIn('RandomizedDelaySec=10min',timer)
        with tempfile.TemporaryDirectory() as directory,\
             patch.object(update_background,'USER_UNIT_DIR',Path(directory)),\
             patch.object(update_background.sys,'platform','linux'),\
             patch.object(update_background.shutil,'which',return_value=None):
            self.assertFalse(update_background.install_user_timer(True))
            self.assertTrue((Path(directory)/update_background.SERVICE_NAME).is_file())
            self.assertTrue((Path(directory)/update_background.TIMER_NAME).is_file())


    def test_old_timer_is_migrated_and_restarted_once(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(update_background,'USER_UNIT_DIR',Path(directory)), \
             patch.object(update_background.sys,'platform','linux'), \
             patch.object(update_background.shutil,'which',return_value='/bin/systemctl'), \
             patch.object(update_background.subprocess,'run') as run:
            Path(directory,update_background.TIMER_NAME).write_text('[Timer]\\nOnUnitInactiveSec=2min\\n')
            self.assertTrue(update_background.install_user_timer(True))
            self.assertTrue(any('restart' in c.args[0] for c in run.call_args_list))
            self.assertIn('60min',Path(directory,update_background.TIMER_NAME).read_text())
            self.assertIn('OnStartupSec=45s',Path(directory,update_background.LOGIN_TIMER_NAME).read_text())
            run.reset_mock()
            self.assertTrue(update_background.install_user_timer(True))
            self.assertFalse(any('restart' in c.args[0] for c in run.call_args_list))
            run.reset_mock()
            self.assertTrue(update_background.install_user_timer(False))
            self.assertTrue(any('disable' in c.args[0] and update_background.LOGIN_TIMER_NAME in c.args[0] for c in run.call_args_list))


if __name__=='__main__':unittest.main()
