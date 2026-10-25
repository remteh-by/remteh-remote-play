"""Invalid owner funding configuration must never become a visible destination."""
import importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('funding',ROOT/'scripts/generate-support.py');funding=importlib.util.module_from_spec(spec);spec.loader.exec_module(funding)

class FundingConfig(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  for name in ('design-system/support.json','design-system/supporters.json','localization/support.json'):
   path=self.root/name;path.parent.mkdir(exist_ok=True);shutil.copy2(ROOT/name,path)
  self.patch=patch.object(funding,'ROOT',self.root);self.patch.start()
 def tearDown(self):self.patch.stop();self.temp.cleanup()
 def change(self,mutate):
  p=self.root/'design-system/support.json';x=json.loads(p.read_text());mutate(x);p.write_text(json.dumps(x))
 def test_empty_disabled_methods_are_not_distributed(self):
  payload=funding.prepare();self.assertEqual([x['id'] for x in payload['methods']],['kofi']);self.assertEqual(payload['supporters'],[])
  self.assertEqual(len(payload['texts']),16)
 def test_enabled_empty_destination_is_rejected(self):
  self.change(lambda x:x['methods'][1].update(enabled=True))
  with self.assertRaises(ValueError):funding.prepare()
 def test_nonfinite_funding_progress_is_rejected(self):
  self.change(lambda x:x['goals'][0].update(raised_usd=float('nan')))
  with self.assertRaises(ValueError):funding.prepare()
 def test_non_https_support_link_is_rejected(self):
  self.change(lambda x:x['methods'][0].update(url='http://example.com/'))
  with self.assertRaises(ValueError):funding.prepare()
