"""Collector failures cannot block static pages or the unchanged signed feed."""
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
collector=module('optional_stats','scripts/site-download-stats.py');builder=module('site_builder_fallback','scripts/build-site.py')
class OptionalStatistics(unittest.TestCase):
 def test_api_exit_empty_invalid_and_timeout_build_site_and_channel(self):
  programs=['raise SystemExit(22)',"from pathlib import Path;import sys;Path(sys.argv[-1]).write_text('')","from pathlib import Path;import sys;Path(sys.argv[-1]).write_text('{broken')","from pathlib import Path;import sys;Path(sys.argv[-1]).write_text('null')",'import time;time.sleep(2)']
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory)
   for index,program in enumerate(programs):
    with self.subTest(index=index):
     script=root/'collector.py';script.write_text(program);output=root/'stats.json';summary=root/'summary.md'
     with patch.dict('os.environ',{'GITHUB_STEP_SUMMARY':str(summary)}):self.assertFalse(collector.collect(output,[sys.executable,str(script)],timeout=.2))
     self.assertEqual(json.loads(output.read_text()),{'schema':1,'available':False})
     out=root/'site'
     with patch('sys.argv',['build-site.py','--out',str(out),'--download-stats',str(output)]):builder.main()
     self.assertNotIn('id="download-stats"',(out/'index.html').read_text())
     for name in ['index.json','index.sig']:self.assertEqual((out/'updates'/name).read_bytes(),(ROOT/'website/updates'/name).read_bytes())
     self.assertIn('not unique people',(out/'docs/DOWNLOADS.md').read_text())
     self.assertIn('without counters',summary.read_text())
 def test_english_fallback_cannot_be_published(self):
  data=json.loads((ROOT/'localization/site.json').read_text());data['ja']['full_guide']=data['en']['full_guide']
  with self.assertRaisesRegex(ValueError,'ja.full_guide'):builder.validate_translations(data)
