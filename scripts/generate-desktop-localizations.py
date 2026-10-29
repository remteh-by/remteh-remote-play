#!/usr/bin/env python3
"""Generate the packaged desktop catalog; reject missing keys/placeholders."""
import argparse,json,string
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def generate(check=False):
    source=json.loads((ROOT/'localization/desktop.json').read_text())
    expected={'en','ru','uk','pl','de','fr','es','it','pt','tr','zh','ja','ko','ar','hi','id'}
    if set(source)!=expected:raise ValueError('Desktop language set differs')
    fields=lambda value:{key for _,key,_,_ in string.Formatter().parse(value) if key is not None}
    for language,words in source.items():
        if set(words)!=set(source['en']):raise ValueError('Incomplete desktop catalog: '+language)
        for key,value in words.items():
            if not isinstance(value,str) or not value.strip() or fields(value)!=fields(source['en'][key]):raise ValueError((language,key))
    target=ROOT/'desktop/linux/assets/desktop-translations.json'
    raw=(json.dumps(source,ensure_ascii=False,indent=2)+'\n').encode()
    if check:
        if not target.is_file() or target.read_bytes()!=raw:raise ValueError('Run scripts/generate-desktop-localizations.py')
    else:target.write_bytes(raw)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');generate(parser.parse_args().check)
