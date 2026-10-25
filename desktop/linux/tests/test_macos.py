import importlib
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from PyQt5.QtCore import QSettings,QByteArray
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import macos_engine


class MacIntegrationTests(unittest.TestCase):
    def test_registration_import_reads_local_native_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/'engine.ini';settings=QSettings(str(file),QSettings.IniFormat)
            settings.beginWriteArray('registered_hosts',1);settings.setArrayIndex(0)
            for key,value in {'target':1000100,'server_nickname':'Test PS5','server_mac':QByteArray(b'123456'),
                'rp_regist_key':QByteArray(b'r'*16),'rp_key_type':1,'rp_key':QByteArray(b'k'*16)}.items():settings.setValue(key,value)
            settings.endArray();settings.sync()
            with patch.object(macos_engine,'QSettings',lambda *args:QSettings(str(file),QSettings.IniFormat)):
                hosts=macos_engine.paired_hosts()
            self.assertEqual(len(hosts),1)
            self.assertEqual(hosts[0][1]['server_mac'],b'123456'.hex())
            self.assertEqual(hosts[0][1]['rp_key'],(b'k'*16).hex())

    def test_frozen_helpers_do_not_create_the_dashboard(self):
        import macos_main
        with patch.object(sys,'argv',['Deckivo','--internal-engine']),patch('macos_supervisor.main',return_value=0) as engine:
            self.assertEqual(macos_main.main(),0);engine.assert_called_once()
        with patch.object(sys,'argv',['Deckivo','--internal-update','descriptor','123']),patch('install_update.main') as install:
            self.assertEqual(macos_main.main(),0);install.assert_called_once_with('descriptor','123')
