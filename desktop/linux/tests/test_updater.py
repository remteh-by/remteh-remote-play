import base64
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from updater import candidate,valid_base,verify_signature,UpdateCancelled,fetch,channel_base,DEFAULT_CHANNEL
from install_update import extract


class UpdatePolicyTests(unittest.TestCase):
    def test_public_channel_migration_and_signed_asset_origin(self):
        self.assertEqual(channel_base({}),DEFAULT_CHANNEL)
        self.assertEqual(channel_base({'base_url':'http://192.168.1.50/private/'}),DEFAULT_CHANNEL)
        self.assertEqual(channel_base({'base_url':'http://192.168.1.50/private/','private_preview':True}),'http://192.168.1.50/private/')
        row=self.row();row['url']='https://example.com/foreign.zip'
        with self.assertRaises(ValueError):candidate({'schema':1,'packages':[row]},'macos-arm64','0.5.0',1)
    def row(self,**changes):
        return dict(platform='macos-arm64',version='0.5.1',build=4,filename='Deckivo-macos-0.5.1-b4.zip',bytes=1,sha256='a'*64,**changes)

    def test_installed_build_never_updates_to_itself(self):
        index={'schema':1,'packages':[self.row()]}
        self.assertIsNone(candidate(index,'macos-arm64','0.5.1',4))
        self.assertIsNone(candidate(index,'macos-arm64','0.6.0',1))
        self.assertEqual(candidate(index,'macos-arm64','0.5.1',3)['build'],4)
        self.assertIsNone(candidate(index,'linux-switch-arm64','0.5.1',3))

    def test_public_cleartext_channels_and_path_injection_are_rejected(self):
        self.assertFalse(valid_base('http://example.com/private/'))
        self.assertFalse(valid_base('https://user:secret@example.com/private/'))
        self.assertFalse(valid_base('https://example.com/private/?token=secret'))
        self.assertTrue(valid_base('http://192.168.1.50/private/'))
        row=self.row();row['filename']='../outside.zip'
        with self.assertRaises(ValueError):candidate({'schema':1,'packages':[row]},'macos-arm64','0.5.0',1)

    def test_cancel_prevents_even_opening_the_network(self):
        with self.assertRaises(UpdateCancelled):fetch('https://example.com/',1024,cancel=lambda:True)

    def test_manifest_tamper_and_wrong_signing_key_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);private=root/'key.pem';public=root/'public.der';wrong=root/'wrong.der'
            subprocess.run(['openssl','genpkey','-algorithm','RSA','-pkeyopt','rsa_keygen_bits:2048','-out',str(private)],check=True,capture_output=True)
            subprocess.run(['openssl','pkey','-in',str(private),'-pubout','-outform','DER','-out',str(public)],check=True,capture_output=True)
            raw=json.dumps({'schema':1,'packages':[]}).encode();payload=root/'payload';payload.write_bytes(raw)
            signature=subprocess.run(['openssl','dgst','-sha256','-sign',str(private),str(payload)],check=True,capture_output=True).stdout
            encoded=base64.b64encode(signature);verify_signature(raw,encoded,public)
            with self.assertRaises(ValueError):verify_signature(raw+b' ',encoded,public)
            subprocess.run(['openssl','genpkey','-algorithm','RSA','-pkeyopt','rsa_keygen_bits:2048','-out',str(private)],check=True,capture_output=True)
            subprocess.run(['openssl','pkey','-in',str(private),'-pubout','-outform','DER','-out',str(wrong)],check=True,capture_output=True)
            with self.assertRaises(ValueError):verify_signature(raw,encoded,wrong)


class ArchiveTests(unittest.TestCase):
    def archive(self,root,links,filename='Deckivo.app/Versions/A/engine'):
        path=root/'update.zip'
        with zipfile.ZipFile(path,'w') as archive:
            archive.writestr(filename,b'engine')
            for name,target in links:
                item=zipfile.ZipInfo(name);item.external_attr=(stat.S_IFLNK|0o777)<<16
                archive.writestr(item,target)
        return path

    def test_internal_framework_alias_survives_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);stage=root/'stage';stage.mkdir()
            path=self.archive(root,[('Deckivo.app/Versions/Current','A'),('Deckivo.app/engine','Versions/Current/engine')])
            extract(path,stage)
            self.assertTrue((stage/'Deckivo.app/engine').is_symlink())
            self.assertEqual((stage/'Deckivo.app/engine').read_bytes(),b'engine')

    def test_traversal_and_external_symlinks_are_rejected(self):
        for links,filename in [([], '../outside'),([('Deckivo.app/engine','/etc/passwd')],'safe'),([('Deckivo.app/link','../../outside')],'safe')]:
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory);stage=root/'stage';stage.mkdir()
                with self.assertRaises(ValueError):extract(self.archive(root,links,filename),stage)


if __name__=='__main__':unittest.main()
