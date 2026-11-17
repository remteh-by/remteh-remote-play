import importlib.util
from pathlib import Path
import unittest

SPEC=importlib.util.spec_from_file_location('public_release',Path(__file__).resolve().parents[1]/'scripts/verify-public-release.py')
checker=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(checker)

class PublicReleaseTests(unittest.TestCase):
    def asset(self,tag,name):
        return dict(name=name,url='https://github.com/remteh-by/remteh-remote-play/releases/download/'+tag+'/'+name,bytes=1,sha256='a'*64)
    def test_independent_android_and_desktop_releases_are_grouped(self):
        doc=dict(version='0.8.12',desktop_version='0.8.11',assets=[self.asset('v0.8.12','android.apk'),self.asset('v0.8.11','desktop.zip')])
        self.assertEqual(set(checker.group_assets(doc)),{'v0.8.12','v0.8.11'})
    def test_external_host_is_rejected_before_any_authenticated_request(self):
        row=self.asset('v0.8.12','android.apk');row['url']=row['url'].replace('github.com','example.invalid')
        with self.assertRaises(ValueError):checker.group_assets(dict(version='0.8.12',assets=[row]))
    def test_duplicate_or_unbound_asset_is_rejected(self):
        row=self.asset('v0.8.12','android.apk')
        for rows in ([row,row],[dict(row,name='different.apk')]):
            with self.subTest(rows=rows),self.assertRaises(ValueError):checker.group_assets(dict(version='0.8.12',assets=rows))

if __name__=='__main__':unittest.main()
