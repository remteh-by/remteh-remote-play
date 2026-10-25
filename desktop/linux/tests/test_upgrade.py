import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import upgrade


class UpgradeTransaction(unittest.TestCase):
    def run_upgrade(self,fail=False):
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
            with patch.object(upgrade,'DEST',dest),patch.object(upgrade,'PRIVATE',private),\
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

    def test_upgrade_retains_pairing(self):self.run_upgrade()
    def test_mid_upgrade_failure_restores_old_files(self):self.run_upgrade(fail=True)


if __name__=='__main__':unittest.main()
