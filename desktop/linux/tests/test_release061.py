import base64
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rsa_verify import verify,public_numbers,element,integer,SHA256_INFO
from updater import allowed_redirect,DEFAULT_CHANNEL,FUTURE_CHANNEL,valid_base
import install_update
import upgrade
import support_policy


class SignatureTests(unittest.TestCase):
    def test_existing_published_signature_and_truncation(self):
        root=Path(__file__).resolve().parents[3]
        payload=(root/'website/updates/index.json').read_bytes()
        signature=(root/'website/updates/index.sig').read_bytes()
        key=(root/'design-system/update-public.der').read_bytes()
        verify(payload,signature,key)
        for data,sig in ((payload+b' ',signature),(payload,signature[:-4]),(payload,base64.b64encode(b'\0'*384))):
            with self.assertRaises(ValueError):verify(data,sig,key)
        with self.assertRaises(ValueError):public_numbers(key+b'\0')

    def test_padding_and_out_of_range_are_not_accepted(self):
        # Test-only key; runtime verification never executes OpenSSL.
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            key=Path(directory)/'test.pem';der=Path(directory)/'test.der';public=Path(directory)/'public.der'
            subprocess.run(['openssl','genrsa','-out',str(key),'2048'],check=True,capture_output=True)
            subprocess.run(['openssl','rsa','-in',str(key),'-outform','DER','-out',str(der)],check=True,capture_output=True)
            subprocess.run(['openssl','pkey','-in',str(key),'-pubout','-outform','DER','-out',str(public)],check=True,capture_output=True)
            body,_=element(der.read_bytes(),0,0x30);_,pos=integer(body,0)
            if body[pos] == 0x30:  # OpenSSL 3 emits PKCS#8; LibreSSL emits PKCS#1.
                _,pos=element(body,pos,0x30);raw,_=element(body,pos,0x04)
                body,_=element(raw,0,0x30);_,pos=integer(body,0)
            n,pos=integer(body,pos);_,pos=integer(body,pos);d,_=integer(body,pos)
            size=(n.bit_length()+7)//8;digest=SHA256_INFO+hashlib.sha256(b'payload').digest()
            good=b'\0\1'+b'\xff'*(size-len(digest)-3)+b'\0'+digest
            def signed(encoded):return base64.b64encode(pow(int.from_bytes(encoded,'big'),d,n).to_bytes(size,'big'))
            verify(b'payload',signed(good),public.read_bytes())
            bad=good[:10]+b'\xfe'+good[11:]
            with self.assertRaises(ValueError):verify(b'payload',signed(bad),public.read_bytes())
            with self.assertRaises(ValueError):verify(b'payload',base64.b64encode(n.to_bytes(size,'big')),public.read_bytes())
            with self.assertRaises(ValueError):verify(b'payload',signed(good),(Path(__file__).resolve().parents[3]/'design-system/update-public.der').read_bytes())

    def test_private_preview_excludes_documentation_networks(self):
        for host in ('192.168.0.10','10.0.0.10','127.0.0.1'):
            self.assertTrue(valid_base('http://'+host+'/private/'))
        for host in ('192.0.2.10','198.51.100.10','203.0.113.10','8.8.8.8'):
            self.assertFalse(valid_base('http://'+host+'/private/'))

    def test_only_exact_owned_metadata_redirect_is_allowed(self):
        self.assertTrue(allowed_redirect(DEFAULT_CHANNEL+'index.json',FUTURE_CHANNEL+'index.json'))
        self.assertTrue(allowed_redirect(DEFAULT_CHANNEL+'index.sig',FUTURE_CHANNEL+'index.sig'))
        for target in ('https://example.com/updates/index.json',FUTURE_CHANNEL+'index.sig',FUTURE_CHANNEL+'index.json?x=1',FUTURE_CHANNEL+'../other'):
            self.assertFalse(allowed_redirect(DEFAULT_CHANNEL+'index.json',target))
        self.assertFalse(allowed_redirect(DEFAULT_CHANNEL+'other',FUTURE_CHANNEL+'other'))


class Child:
    pid=42
    def __init__(self,events):self.events=events;self.running=True
    def poll(self):return None if self.running else 0
    def terminate(self):self.events.append('stop');self.running=False
    def wait(self,timeout):return 0


class StartupTests(unittest.TestCase):
    def test_linux_missing_ack_restores_files_before_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);dest=root/'deckivo';dest.mkdir();backup=root/'deckivo-backups/before-test';backup.mkdir(parents=True)
            (dest/'deckivo.py').write_text('new');(dest/'new.py').write_text('new');(dest/'registration.json').write_text('keep pairing')
            (backup/'deckivo.py').write_text('old');(backup/'receipt.json').write_text(json.dumps({'files':['deckivo.py','new.py'],'removed':[],'previous':['deckivo.py']}))
            events=[];child=Child(events)
            def restore():
                self.assertFalse(child.running);upgrade.restore_backup(backup);events.append('restore')
            with patch.object(upgrade,'DEST',dest),patch.object(install_update,'PRIVATE',root/'private'),patch.object(install_update,'wait_for_ack',return_value=False):
                with self.assertRaises(ValueError):install_update.confirm_or_rollback({'sha256':'a'*64,'build':10},'nonce',child,restore,lambda:events.append('restart'))
            self.assertEqual(events,['stop','restore','restart']);self.assertEqual((dest/'deckivo.py').read_text(),'old')
            self.assertFalse((dest/'new.py').exists());self.assertEqual((dest/'registration.json').read_text(),'keep pairing')

    def test_mac_missing_ack_stops_new_process_before_bundle_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            events=[];child=Child(events)
            with patch.object(install_update,'PRIVATE',Path(directory)),patch.object(install_update,'wait_for_ack',return_value=False):
                with self.assertRaises(ValueError):install_update.confirm_or_rollback({'sha256':'b'*64,'build':10},'nonce',child,lambda:events.append('rename bundle'),lambda:events.append('restart'))
            self.assertEqual(events,['stop','rename bundle','restart'])

    def test_live_child_is_never_restored_underneath(self):
        events=[]
        class Refuses(Child):
            def terminate(self):events.append('stop')
            def wait(self,timeout):raise subprocess.TimeoutExpired('updated app',timeout)
        child=Refuses(events)
        with patch.object(install_update,'wait_for_ack',return_value=False):
            with self.assertRaises(RuntimeError):install_update.confirm_or_rollback({},'nonce',child,lambda:events.append('restore'),lambda:events.append('restart'))
        self.assertEqual(events,['stop'])

    def test_mac_readiness_rejects_bad_config_and_missing_engine(self):
        import update_ui,macos_engine
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);engine=root/'engine';config=root/'preferences.json'
            with patch.object(update_ui,'PRIVATE',root),patch.object(update_ui,'CONFIG',config),patch.object(update_ui.sys,'platform','darwin'),patch.object(macos_engine,'resolve_engine',side_effect=lambda:engine if engine.is_file() else None):
                self.assertFalse(update_ui.startup_ready(None))
                engine.write_bytes(b'engine');config.write_text('{broken')
                self.assertFalse(update_ui.startup_ready(None))
                config.write_text('{}');self.assertTrue(update_ui.startup_ready(None))
                (root/'registration.json').write_text('[]');self.assertFalse(update_ui.startup_ready(None))

    def test_ack_must_match_child_and_transaction(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);child=Child([])
            with patch.object(install_update,'PRIVATE',root):
                (root/'update-ack.json').write_text(json.dumps({'transaction':'wrong','pid':42}))
                self.assertFalse(install_update.wait_for_ack('nonce',child,timeout=.001))
                (root/'update-ack.json').write_text(json.dumps({'transaction':'nonce','pid':41}))
                self.assertFalse(install_update.wait_for_ack('nonce',child,timeout=.001))
                (root/'update-ack.json').write_text(json.dumps({'transaction':'nonce','pid':42}))
                self.assertTrue(install_update.wait_for_ack('nonce',child,timeout=.1))
            self.assertEqual(install_update.STARTUP_TIMEOUT,120)


class ThanksTests(unittest.TestCase):
    def test_clean_threshold_and_bounded_reminders(self):
        self.assertFalse(support_policy.due(support_policy.complete({},600,False),0))
        self.assertFalse(support_policy.due(support_policy.complete({},599,True),0))
        state=support_policy.complete({},600,True);self.assertTrue(support_policy.due(state,0))
        for count in range(3):
            state=support_policy.shown(state);self.assertEqual(state['shows'],count+1)
            state=support_policy.action(state,'later',count*support_policy.LATER_SECONDS)
            self.assertFalse(support_policy.due(state,state['next_at']-1))
        self.assertFalse(support_policy.due(state,10**12))
        state=support_policy.action(support_policy.complete({},600,True),'never',0)
        self.assertFalse(support_policy.due(state,10**12))


if __name__=='__main__':unittest.main()
