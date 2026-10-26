"""Rendered HTML boundaries, without changing production support/config files."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('site_builder',ROOT/'scripts/build-site.py')
builder=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(builder)


class SiteGenerationTests(unittest.TestCase):
    def test_threshold_and_verified_funding_amounts_in_all_languages(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture=Path(directory)
            for name in ('website','design-system','localization'):
                shutil.copytree(ROOT/name,fixture/name)
            settings=json.loads((fixture/'design-system/site.json').read_text())
            threshold=settings['site']['downloads']['public_min_packages']
            support=json.loads((fixture/'website/support.json').read_text())
            for count,expected in ((threshold-1,0),(threshold,1)):
                with self.subTest(package_downloads=count):
                    # A fully valid one-release snapshot with no network or real donations.
                    platforms={'android':count,'macos':0,'linux':0,'bundle':0}
                    release={'tag':'v0.8.3','url':'https://github.com/remteh-by/remteh-remote-play/releases/tag/v0.8.3',
                        'published_at':'2026-10-26T00:00:00Z','prerelease':True,'package_total':count,
                        'total_downloads':count,'platforms':platforms,'assets':[{'name':'fixture.apk','count':count,'category':'android'}]}
                    snapshot={'schema':1,'repository':'remteh-by/remteh-remote-play','generated_at':'2026-10-26T00:00:00Z',
                        'package_total':count,'total_downloads':count,'platforms':platforms,'releases':[release]}
                    stats=fixture/'stats.json';stats.write_text(json.dumps(snapshot))
                    support['goals'][0].update(target_usd=99,raised_usd=12 if expected else None)
                    (fixture/'website/support.json').write_text(json.dumps(support))
                    out=fixture/'rendered'
                    with patch.object(builder,'ROOT',fixture),patch('sys.argv',['build-site.py','--out',str(out),'--download-stats',str(stats)]):
                        builder.main()
                    for lang in builder.NAMES:
                        page=out/('index.html' if lang=='en' else lang+'/index.html')
                        soup=BeautifulSoup(page.read_text(),'html.parser')
                        self.assertEqual(len(soup.select('#download-stats')),expected,lang)
                        bars=soup.select('#support progress')
                        self.assertEqual(len(bars),expected,lang)
                        if bars:self.assertEqual(bars[0]['value'],'12')
                        self.assertNotIn(support['texts'][lang]['progress_unknown'],soup.get_text())
                    self.assertIn(f'**{count}**',(out/'docs/DOWNLOADS.md').read_text())


if __name__=='__main__':unittest.main()
