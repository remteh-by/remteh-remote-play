import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from connection_diagnostics import summarize
class ConnectionDiagnosticsTests(unittest.TestCase):
 def facts(self):return dict(host_configured=True,paired=True,probe_state='online',probe_age=2,engine_present=True,decoder_active=False,input_present=False,profile='smooth')
 def test_stale_probe_does_not_establish_connectivity(self):
  facts=self.facts();facts['probe_age']=60
  report=summarize(**facts)
  self.assertEqual(report['checks'][2]['status'],'not-measured')
 def test_discovery_does_not_claim_video_or_input_success(self):
  report=summarize(**self.facts());self.assertEqual(report['checks'][2]['status'],'observed')
  self.assertEqual(report['checks'][4]['status'],'not-measured');self.assertEqual(report['checks'][5]['status'],'not-measured')
 def test_profile_is_allowlisted_and_missing_components_are_specific(self):
  facts=self.facts();facts.update(profile='private-value',paired=False,engine_present=False,probe_state='offline')
  report=summarize(**facts);self.assertNotIn('private-value',str(report));self.assertEqual(report['checks'][1]['status'],'missing');self.assertEqual(report['checks'][3]['status'],'missing');self.assertEqual(report['checks'][2]['status'],'not-observed')
