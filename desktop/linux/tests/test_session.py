import json
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from session import preferences,telemetry,session_record,safe_report,log_stage,duration,history_records


class SessionSafety(unittest.TestCase):
    def test_corrupt_preferences_cannot_select_arbitrary_profile(self):
        for bad in (None,[],{'quality':999},{'quality':'0'},{'quality':True}):
            self.assertEqual(preferences(bad)['quality'],0)
        self.assertEqual(preferences({'quality':2,'quality_schema':2})['quality'],2)
        self.assertEqual(preferences({'host':'$(touch /tmp/bad)'})['host'],'')

    def test_existing_owner_preferences_survive_migration(self):
        old={'host':'192.0.2.10','language':'auto','quality':1,'quality_schema':2}
        migrated=preferences(old)
        self.assertTrue(all(migrated[k]==v for k,v in old.items()))
        self.assertTrue(migrated['fullscreen'])

    def test_untrusted_metrics_are_bounded_and_private(self):
        value=telemetry({'frames':-1,'width':99999,'decode_fps':math.nan,'decoder':'<script>',
                         'rp_key':'secret','exclusive':'yes','elapsed_ms':1.2})
        self.assertEqual(value,{'exclusive':False})
        self.assertEqual(telemetry({'decode_fps':59.94})['decode_fps'],59.9)

    def test_report_cannot_include_pairing_network_or_raw_log(self):
        value=safe_report('playing',{'host':'192.0.2.10','rp_key':'PRIVATE'},
            {'frames':120,'decode_fps':60,'pid':123,'rp_key':'KEY','log':'secret'},True,4)
        report=json.dumps(value)
        for secret in ('192.0.2.10','PRIVATE','KEY','secret','"pid"'):
            self.assertNotIn(secret,report)
        self.assertEqual(value['requested']['fps'],60)
        self.assertEqual(value['observed']['frames'],120)

    def test_session_summary_measures_actual_frames_not_requested_fps(self):
        record=session_record('2026-10-25T12:00:00',20,0,
                              {'frames':900,'elapsed_ms':20000},'finished')
        self.assertEqual(record['average_decode_fps'],45)
        self.assertEqual(record['seconds'],20)

    def test_raw_error_text_is_not_exposed(self):
        self.assertEqual(log_stage('token=secret Session has quit: error'),'error')
        self.assertEqual(log_stage('token=secret'),'connecting')

    def test_time_format(self):
        self.assertEqual(duration(65),'01:05')
        self.assertEqual(duration(3605),'1:00:05')
        self.assertEqual(duration(-3),'00:00')

    def test_history_corruption_is_skipped_and_measured_average_preserved(self):
        row=session_record('2026-10-25',20,0,{'frames':900,'elapsed_ms':20000},'finished')
        clean=history_records([None,{'quality':'bad'},row])
        self.assertEqual(len(clean),1)
        self.assertEqual(clean[0]['average_decode_fps'],45)


if __name__=='__main__':unittest.main()
