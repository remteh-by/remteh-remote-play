import os,sys,unittest
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import support_policy as policy
import update_ui
from session import VERSION
from build_meta import BUILD
class AuditPolicy(unittest.TestCase):
 def test_only_current_clean_long_session_qualifies_once(self):
  stale=policy.complete({},900,True)
  for seconds,clean in ((0,False),(20,False),(20,True),(599,True),(900,False)):
   state=policy.complete(stale,seconds,clean)
   state,show=policy.consume(state,10**9);self.assertFalse(show)
  state,show=policy.consume(policy.complete(stale,600,True),10**9);self.assertTrue(show)
  self.assertFalse(policy.consume(state,10**9)[1])
 def test_deferred_or_suppressed_decision_is_consumed(self):
  state,show=policy.consume(policy.complete({},600,True),0,False)
  self.assertFalse(show);self.assertFalse(policy.consume(state,100)[1])
 def test_cooldown_never_and_three_displays(self):
  state=policy.action(policy.shown(policy.complete({},900,True)),'later',100)
  self.assertFalse(policy.due(policy.complete(state,600,True),100+policy.LATER_SECONDS-1))
  self.assertTrue(policy.due(policy.complete(state,600,True),100+policy.LATER_SECONDS))
  for shows in (3,100):self.assertFalse(policy.due(policy.complete({'shows':shows},600,True),10**9))
  self.assertFalse(policy.due(policy.complete({'disabled':True},600,True),10**9))
 def test_startup_check_uses_success_age_and_same_build(self):
  for record,expected in (({},True),({'time':100,'version':VERSION,'build':BUILD},False),({'time':-4000,'version':VERSION,'build':BUILD},True),({'time':10000,'version':VERSION,'build':BUILD},True),({'time':100,'version':'old','build':1},True)):
   with self.subTest(record=record),patch.object(update_ui,'load_json',return_value=record):self.assertEqual(update_ui.startup_check_due(1000),expected)
