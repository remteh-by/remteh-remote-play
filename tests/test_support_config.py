"""Invalid owner funding configuration must never become a visible destination."""
import importlib.util,json,shutil,tempfile,unittest
from xml.etree import ElementTree
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
  self.change(lambda x:x['methods'].append(dict(id='unused',enabled=False,url='')))
  payload=funding.prepare();self.assertNotIn('unused',[x['id'] for x in payload['methods']]);self.assertEqual(payload['supporters'],[])
  self.assertEqual(len(payload['texts']),16)
 def test_enabled_empty_destination_is_rejected(self):
  self.change(lambda x:x['methods'][0].update(url=''))
  with self.assertRaises(ValueError):funding.prepare()
 def test_all_owner_destinations_have_translated_status_and_options(self):
  expected={'kofi':'https://ko-fi.com/pavelzayats'}
  payload=funding.prepare();self.assertEqual({x['id']:x['url'] for x in payload['methods']},expected)
  for method in payload['methods']:
   for copy in payload['texts'].values():
    self.assertTrue(copy['method_status_'+method['status']].strip())
    self.assertTrue(copy['method_cadence_'+method['cadence']].strip())
  self.assertTrue(all(m['status']=='configured' for m in payload['methods']))
 def test_unknown_status_is_rejected_instead_of_implying_payment_readiness(self):
  self.change(lambda x:x['methods'][0].update(status='ready'))
  with self.assertRaises(ValueError):funding.prepare()
 def test_credentials_in_destination_are_rejected(self):
  self.change(lambda x:x['methods'][0].update(url='https://user:password@example.com/'))
  with self.assertRaises(ValueError):funding.prepare()
 def test_web_qr_quiet_zone_survives_dark_github_pages_without_styles(self):
  for method in funding.prepare()['methods']:
   image=ElementTree.fromstring((ROOT/'website/assets/support'/(method['id']+'.svg')).read_bytes())
   rectangles=image.findall('{http://www.w3.org/2000/svg}rect')
   self.assertTrue(any(rect.get('fill') in ('white','#fff','#ffffff') and rect.get('width')=='100%' and rect.get('height')=='100%' for rect in rectangles),method['id'])
 def test_nonfinite_funding_progress_is_rejected(self):
  self.change(lambda x:x['goals'][0].update(raised_usd=float('nan')))
  with self.assertRaises(ValueError):funding.prepare()
 def test_non_https_support_link_is_rejected(self):
  self.change(lambda x:x['methods'][0].update(url='http://example.com/'))
  with self.assertRaises(ValueError):funding.prepare()
