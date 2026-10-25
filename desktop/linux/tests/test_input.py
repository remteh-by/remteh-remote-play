import math
from pathlib import Path
import socket
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from keyboard_mouse import InputState,InputTransport
from session import preferences,PRESETS,session_record

class EmulatedInputTests(unittest.TestCase):
    def unpack(self,state,at=None):return struct.unpack('<4sII6h',state.packet(at))
    def test_movement_is_normalized_and_opposites_cancel(self):
        s=InputState();s.key('W',True);s.key('D',True)
        p=self.unpack(s);self.assertLessEqual(math.hypot(p[3],p[4]),32768)
        s.key('A',True);self.assertEqual(self.unpack(s)[3],0)
    def test_mouse_expires_and_rejects_nonfinite_input(self):
        s=InputState();s.move(100,-100,at=1)
        self.assertEqual(self.unpack(s,1.01)[5:7],(32767,-32767))
        self.assertEqual(self.unpack(s,1.09)[5:7],(0,0))
        s.move(float('nan'),0,at=2);self.assertEqual(self.unpack(s,2)[5:7],(0,0))
    def test_releasing_all_clears_buttons_sticks_and_triggers(self):
        s=InputState();s.key('Space',True);s.mouse_buttons.update(('left','right'));s.move(3,4);s.reset()
        p=self.unpack(s);self.assertEqual(p[2:],(0,0,0,0,0,-32768,-32768))
    def test_rebind_does_not_release_an_action_still_held(self):
        s=InputState(mapping={'C':'cross'});s.key('C',True);s.key('Space',True);s.key('C',False)
        self.assertEqual(self.unpack(s)[2]&1,1)
    def test_recapturing_input_keeps_sequence_monotonic(self):
        a=InputState();first=self.unpack(a)[1];last=self.unpack(a)[1]
        self.assertGreater(last,first);self.assertGreater(self.unpack(InputState())[1],last)
    def test_transport_is_local_and_fixed_size(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as d:
            path=Path(d)/'in.sock'
            with socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM) as receiver:
                receiver.bind(str(path));receiver.settimeout(1)
                sender=InputTransport(path);self.assertTrue(sender.send(InputState().packet()));self.assertEqual(len(receiver.recv(200)),24);sender.close()
    def test_old_mac_profile_migrates_once_without_losing_requested_quality(self):
        with patch('session.sys.platform','darwin'):
            p=preferences({'quality':0});self.assertEqual(PRESETS[p['quality']].height,1080)
            self.assertEqual(preferences(p)['quality'],p['quality'])
    def test_new_1080_profiles_remain_bounded_in_history(self):
        self.assertTrue(all(p.height<=1080 for p in PRESETS))
        self.assertEqual(session_record('',2,4,{},'finished')['quality'],4)
