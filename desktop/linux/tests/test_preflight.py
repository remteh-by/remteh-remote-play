import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from preflight import evaluate
class PreflightTests(unittest.TestCase):
 def fixture(self):
  return dict(system='Linux',architecture='aarch64',os_id='ubuntu',os_version='24.04',python=[3,12],qt=True,display=True,session='x11',free_bytes=3*1024**3,writable=True,commands={'gcc':True,'apt-get':True,'dpkg-deb':True},avcodec='libavcodec.so.60',crypto=True,sdl2=True,existing_runtime=False)
 def test_supported_environment_passes(self):
  self.assertTrue(all(row['passed'] for row in evaluate(self.fixture())))
 def test_wrong_abi_platform_space_and_existing_runtime_get_actionable_stops(self):
  for field,value in [('system','Darwin'),('architecture','x86_64'),('session','wayland'),('avcodec','libavcodec.so.61'),('free_bytes',1),('existing_runtime',True)]:
   facts=self.fixture();facts[field]=value
   failed=[row for row in evaluate(facts) if not row['passed']]
   self.assertTrue(failed);self.assertTrue(all(row['action'] for row in failed))
