#!/usr/bin/env python3
"""Generate funding surfaces from owner configuration; empty methods stay hidden."""
import argparse
import hashlib
import html
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.parse

ROOT=Path(__file__).resolve().parents[1]


def prepare():
    config=json.loads((ROOT/'design-system/support.json').read_text())
    supporters=json.loads((ROOT/'design-system/supporters.json').read_text())
    if not isinstance(supporters,list):raise ValueError('Invalid supporters list')
    for supporter in supporters:
        if set(supporter)!={'name','since'} or not all(isinstance(x,str) and x.strip() for x in supporter.values()):raise ValueError('Invalid supporter')
    methods=[];seen=set()
    for method in config['methods']:
        if not re.fullmatch('[a-z0-9_]+',method['id']) or method['id'] in seen:raise ValueError('Invalid method id')
        seen.add(method['id']);destination=method.get('url') or method.get('address','')
        if method['enabled'] and not destination:raise ValueError('Enabled support method has no owner destination')
        if not method['enabled']:continue
        if method.get('url'):
            parsed=urllib.parse.urlsplit(destination)
            if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password:raise ValueError('Support URL must use HTTPS')
        elif not method.get('network'):raise ValueError('A cryptocurrency address requires its network')
        methods.append(method)
    for goal in config['goals']:
        for field in ('target_usd','raised_usd'):
            number=goal[field]
            if number is not None and (type(number) not in (int,float) or not math.isfinite(number) or number<0):raise ValueError('Invalid owner funding amount')
    texts=json.loads((ROOT/'localization/support.json').read_text())
    payload={'schema':1,'methods':methods,'goals':config['goals'],'supporters':supporters,'texts':texts}
    source=json.dumps([config,supporters,texts],sort_keys=True,ensure_ascii=False).encode()
    payload['source_sha256']=hashlib.sha256(source).hexdigest()
    return payload


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    payload=prepare();raw=(json.dumps(payload,ensure_ascii=False,indent=2)+'\n').encode()
    outputs=[ROOT/'android/app/src/main/res/raw/deckivo_support.json',ROOT/'desktop/linux/assets/support.json',ROOT/'website/support.json']
    if args.check:
        if any(not p.is_file() or p.read_bytes()!=raw for p in outputs):raise SystemExit('Support configuration changed: run scripts/generate-support.py first')
        return
    import qrcode
    import qrcode.image.svg
    for output in outputs:output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(raw)
    for folder in (ROOT/'website/assets/support',ROOT/'desktop/linux/assets/support'):
        folder.mkdir(exist_ok=True)
        for previous in folder.glob('*.svg'):previous.unlink()
        for method in payload['methods']:
            if not method['qr']:continue
            code=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,box_size=8,border=4)
            code.add_data(method.get('url') or method['address']);code.make(fit=True)
            code.make_image(image_factory=qrcode.image.svg.SvgPathImage,fill_color='black',back_color='white').save(folder/(method['id']+'.svg'))
    readme=ROOT/'README.md';text=readme.read_text();begin='<!-- SUPPORT:START -->';end='<!-- SUPPORT:END -->'
    lines=[begin,'### Help Deckivo grow','',payload['texts']['en']['support_body'],'']
    for goal in payload['goals']:lines.append('- '+payload['texts']['en'][goal['title_key']])
    lines.append('')
    for method in payload['methods']:
        target=method.get('url') or method['address'];title=method['title']
        lines.append(f'[{title}]({target})' if method.get('url') else f'{title} · {method["network"]}: `{target}`')
        if method['qr']:lines+=['',f'<img src="website/assets/support/{method["id"]}.svg" alt="Scan {html.escape(title)}" width="180" height="180">','']
    lines.append(payload['texts']['en']['support_note'])
    if payload['supporters']:
        lines+=['','#### Supporters','']+[f'- {html.escape(s["name"])} · {html.escape(s["since"])}' for s in payload['supporters']]
    lines.append(end);block='\n'.join(lines)
    if begin in text:text=text[:text.index(begin)]+block+text[text.index(end)+len(end):]
    else:text=text.replace('### Source and credits',block+'\n\n### Source and credits')
    readme.write_text(text)
    subprocess.run([sys.executable,str(ROOT/'scripts/generate-guides.py')],check=True)
    funding='ko_fi: '+next((m['url'].rstrip('/').split('/')[-1] for m in payload['methods'] if m['id']=='kofi'),'')+'\n' if any(m['id']=='kofi' for m in payload['methods']) else ''
    (ROOT/'.github/FUNDING.yml').write_text(funding+'buy_me_a_coffee: streetpea\ncustom: ["https://remteh-by.github.io/remteh-remote-play/#support"]\n')
    print('Support generated:',len(payload['methods']),'enabled methods;',len(payload['supporters']),'supporters')


if __name__=='__main__':main()
