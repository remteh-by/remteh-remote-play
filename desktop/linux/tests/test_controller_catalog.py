from io import BytesIO
import json
from http.client import HTTPConnection
from functools import partial
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import controller_lab

class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.server=controller_lab.LocalServer(('127.0.0.1',0),partial(controller_lab.Handler,directory=str(controller_lab.ROOT)))
        self.worker=threading.Thread(target=self.server.serve_forever,daemon=True);self.worker.start()
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.worker.join()
    def request(self,suffix):
        connection=HTTPConnection('127.0.0.1',self.server.server_port,timeout=3)
        connection.request('GET','/media/remteh-gamepad/v20261011/firmware.php'+suffix)
        response=connection.getresponse();result=(response.status,response.read(),response.getheader('Content-Type'));connection.close();return result
    def test_binary_download_queries_never_reach_upstream(self):
        with patch.object(controller_lab.urllib.request,'urlopen') as upstream:
            for query in ('?family=0004&version=0x0458','?version=0x0458','?download=1'):
                self.assertEqual(self.request(query)[0],400)
            upstream.assert_not_called()
    def test_only_version_json_is_returned(self):
        catalog={'versions':{'0004':'0x0458','wrong':'0x9999','000B':'file.bin'},'checked_at':'2026-10-26T00:00:00Z','stale':False,
            'artifacts':{'0004':{'download_url':'/binary','downloaded':True}},'secret':'not forwarded'}
        with patch.object(controller_lab.urllib.request,'urlopen',return_value=BytesIO(json.dumps(catalog).encode())) as upstream:
            status,raw,kind=self.request('')
        self.assertEqual(status,200);self.assertEqual(kind,'application/json')
        self.assertEqual(json.loads(raw),{'versions':{'0004':'0x0458'},'stale':False,'checked_at':catalog['checked_at']})
        self.assertEqual(upstream.call_args.args[0].full_url,'https://remteh.by/media/remteh-gamepad/v20261011/firmware.php')
    def test_invalid_upstream_is_not_served_as_a_binary(self):
        with patch.object(controller_lab.urllib.request,'urlopen',return_value=BytesIO(b'\x00binary firmware')):
            self.assertEqual(self.request('')[0],503)
if __name__=='__main__':unittest.main()
