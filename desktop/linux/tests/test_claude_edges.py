"""Claude independent edge tests for Deckivo 0.8.3 desktop (isolated; no network)."""
import io, os, sys, json, stat, zipfile, tempfile, unittest
from pathlib import Path
SRC = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(SRC))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
REL = SRC.parents[1]/'tests/fixtures/0.8.3'; KEY = SRC/'assets/update-public.der'
import rsa_verify, updater, support_policy

class Signature(unittest.TestCase):
    def test_published_index_verifies(self):
        rsa_verify.verify((REL/'index.json').read_bytes(), (REL/'index.sig').read_bytes(), KEY.read_bytes())
    def test_one_byte_change_rejected(self):
        data = bytearray((REL/'index.json').read_bytes()); data[20] ^= 1
        with self.assertRaises(ValueError): rsa_verify.verify(bytes(data), (REL/'index.sig').read_bytes(), KEY.read_bytes())
    def test_truncated_signature_rejected(self):
        with self.assertRaises(ValueError): rsa_verify.verify((REL/'index.json').read_bytes(), (REL/'index.sig').read_bytes()[:-8], KEY.read_bytes())

class Candidate(unittest.TestCase):
    idx = json.loads((REL/'index.json').read_text())
    def test_same_build_not_offered(self):
        self.assertIsNone(updater.candidate(self.idx, 'macos-arm64', '0.8.3', 19))
    def test_older_client_gets_b19(self):
        self.assertEqual(updater.candidate(self.idx, 'macos-arm64', '0.8.2', 18)['build'], 19)
    def test_foreign_url_rejected(self):
        bad = json.loads(json.dumps(self.idx)); bad['packages'][0]['url'] = 'https://evil.example/x.zip'
        with self.assertRaises(ValueError): updater.candidate(bad, 'macos-arm64', '0.8.2', 18)

class Extract(unittest.TestCase):
    def _zip(self, entries):
        b = io.BytesIO()
        with zipfile.ZipFile(b, 'w') as z:
            for name, data, link in entries:
                info = zipfile.ZipInfo(name)
                if link: info.external_attr = (stat.S_IFLNK | 0o777) << 16
                z.writestr(info, data)
        directory=tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup); p = Path(directory.name)/'a.zip'; p.write_bytes(b.getvalue()); return p
    def _run(self, entries):
        import install_update
        directory=tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        install_update.extract(self._zip(entries), Path(directory.name))
    def test_traversal(self):
        with self.assertRaises(ValueError): self._run([('../evil.txt', b'x', False)])
    def test_absolute(self):
        with self.assertRaises(ValueError): self._run([('/tmp/evil.txt', b'x', False)])
    def test_symlink_escape(self):
        with self.assertRaises(ValueError): self._run([('a/link', b'../../../etc', True)])

class SupportReminder(unittest.TestCase):
    """TZ 11: reminders must not appear after a crash or too-short session."""
    def test_no_reminder_after_crash_once_eligible(self):
        state = support_policy.complete({}, 900, True)            # earlier good 15-min session
        state = support_policy.action(support_policy.shown(state), 'later', 0)  # user pressed Later
        now = 15*24*3600                                           # 15 days later
        state = support_policy.complete(state, 20, False)          # this session crashed after 20 s
        self.assertFalse(support_policy.due(state, now), 'reminder would be shown right after a crashed 20-second session')

if __name__ == '__main__': unittest.main(verbosity=1)
