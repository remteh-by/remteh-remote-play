import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location('package_public_release', ROOT / 'scripts/package-public-release.py')
PACKAGE_RELEASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGE_RELEASE)


class PublicReleasePackagingTests(unittest.TestCase):
    def test_linux_archive_contains_each_installer_file_once(self):
        self.assertIn('upgrade.py', PACKAGE_RELEASE.FILES)
        self.assertEqual(len(PACKAGE_RELEASE.FILES), len(set(PACKAGE_RELEASE.FILES)))
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'linux.zip'
            PACKAGE_RELEASE.build_linux_archive(target)
            with zipfile.ZipFile(target) as archive:
                names = archive.namelist()
                documents = {name: archive.read(name) for name in PACKAGE_RELEASE.LINUX_RELEASE_DOCUMENTS}
        expected = (['desktop/linux/' + name for name in PACKAGE_RELEASE.FILES]
            + list(PACKAGE_RELEASE.LINUX_RELEASE_DOCUMENTS))
        self.assertEqual(names, expected)
        self.assertEqual(names.count('desktop/linux/upgrade.py'), 1)
        self.assertEqual(len(names), len(set(names)))
        for name, content in documents.items():
            self.assertEqual(content, (ROOT / name).read_bytes())

    def test_signed_non_linux_packages_are_preserved(self):
        feed = ROOT / 'website/updates'
        existing = PACKAGE_RELEASE.verified_packages(feed)
        preserved = [row for row in existing if row['platform'] != PACKAGE_RELEASE.LINUX_PLATFORM]
        self.assertTrue(preserved, 'The signed public feed must retain its existing macOS release')

        replacement = {
            'platform': PACKAGE_RELEASE.LINUX_PLATFORM,
            'version': '9.9.9',
            'build': 999,
            'filename': 'Deckivo-Linux-9.9.9-b999-source.zip',
        }
        merged = PACKAGE_RELEASE.replace_linux_package(existing, replacement)

        self.assertEqual(merged[:-1], preserved)
        self.assertEqual(merged[-1], replacement)
        self.assertEqual(sum(row['platform'] == PACKAGE_RELEASE.LINUX_PLATFORM for row in merged), 1)

    def test_changed_feed_is_rejected_before_merge(self):
        source = ROOT / 'website/updates'
        with tempfile.TemporaryDirectory() as directory:
            feed = Path(directory)
            (feed / 'index.json').write_bytes((source / 'index.json').read_bytes() + b' ')
            (feed / 'index.sig').write_bytes((source / 'index.sig').read_bytes())
            with self.assertRaises(ValueError):
                PACKAGE_RELEASE.verified_packages(feed)


if __name__ == '__main__':
    unittest.main()
