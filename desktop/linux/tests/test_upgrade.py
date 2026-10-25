import importlib.util
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import upgrade


class UpgradeTransaction(unittest.TestCase):
    def run_upgrade(self,fail=False,timer_fail=False):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);dest=root/'deckivo';private=root/'private'
            (dest/'runtime/usr/bin').mkdir(parents=True);(dest/'runtime/usr/bin/chiaki').write_text('engine')
            (dest/'native').mkdir();(dest/'native/libdeckivo-tegra.so').write_text('old native')
            (dest/'deckivo.py').write_text('old launcher');(dest/'registration.json').write_text('private pairing')
            original_copy=upgrade.shutil.copy2
            def copy(source,target):
                if fail and Path(target).name=='libdeckivo-tegra.so.upgrade-new':
                    raise OSError('injected disk write failure')
                return original_copy(source,target)
            def compile_adapter(args,check):Path(args[-1]).write_text('new native')
            timer=patch('update_background.install_user_timer',side_effect=OSError('injected timer failure')) if timer_fail else patch('update_background.install_user_timer',return_value=False)
            with timer,patch.object(upgrade,'DEST',dest),patch.object(upgrade,'PRIVATE',private),\
                 patch.object(upgrade.platform,'machine',lambda:'aarch64'),\
                 patch.object(upgrade.subprocess,'run',compile_adapter),patch.object(upgrade.shutil,'copy2',copy):
                if fail:
                    with self.assertRaises(OSError):upgrade.main()
                    self.assertEqual((dest/'deckivo.py').read_text(),'old launcher')
                    self.assertEqual((dest/'native/libdeckivo-tegra.so').read_text(),'old native')
                    self.assertFalse((dest/'launcher.py').exists())
                else:
                    upgrade.main()
                    self.assertTrue((dest/'launcher.py').exists())
                    self.assertEqual((dest/'native/libdeckivo-tegra.so').read_text(),'new native')
                self.assertEqual((dest/'registration.json').read_text(),'private pairing')
                for path in (root/'deckivo-backups').rglob('*'):
                    self.assertNotEqual(path.name,'registration.json')
            if not fail:
                self.assertTrue((dest/'upgrade.py').is_file())
                environment={**os.environ,'PYTHONPATH':str(dest)}
                subprocess.run([sys.executable,'-c','from upgrade import restore_backup; assert callable(restore_backup)'],
                    cwd=root,env=environment,check=True,capture_output=True)

    def test_upgrade_retains_pairing(self):self.run_upgrade()
    def test_mid_upgrade_failure_restores_old_files(self):self.run_upgrade(fail=True)
    def test_timer_setup_failure_does_not_fail_completed_upgrade(self):self.run_upgrade(timer_fail=True)


if __name__=='__main__':unittest.main()
