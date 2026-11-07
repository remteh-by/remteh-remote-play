#!/usr/bin/env python3
"""Generate public support destinations and their honest readiness labels."""
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
CADENCES={'both','monthly','once','profile','app'}
STATUSES={'configured','unverified','review','preparing'}


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
        if type(method['enabled']) is not bool:raise ValueError('Support visibility must be a boolean')
        if method['enabled'] and not destination:raise ValueError('Enabled support method has no owner destination')
        if not method['enabled']:continue
        if method.get('cadence') not in CADENCES or method.get('status') not in STATUSES:
            raise ValueError('Support method requires a known cadence and readiness status')
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
    required={'support_choose','support_open_provider','support_copy_link','support_copied','support_copy_failed','support_provider_note'}
    required|={'method_cadence_'+value for value in CADENCES}
    required|={'method_status_'+value for value in STATUSES}
    for language,copy in texts.items():
        if not required.issubset(copy) or any(not isinstance(copy[key],str) or not copy[key].strip() for key in required):
            raise ValueError('Incomplete support labels: '+language)
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
            # GitHub strips page CSS: web/README images need their own white
            # quiet zone. The native renderer already paints a white pixmap.
            factory=qrcode.image.svg.SvgPathFillImage if folder==ROOT/'website/assets/support' else qrcode.image.svg.SvgPathImage
            code.make_image(image_factory=factory,fill_color='black',back_color='white').save(folder/(method['id']+'.svg'))
    readme=ROOT/'README.md';text=readme.read_text();begin='<!-- SUPPORT:START -->';end='<!-- SUPPORT:END -->'
    lines=[begin,'### Help Deckivo grow','',payload['texts']['en']['support_body'],'']
    for goal in payload['goals']:lines.append('- '+payload['texts']['en'][goal['title_key']])
    lines.append('')
    lines+=['| Method | Options | Status |','| --- | --- | --- |']
    for method in payload['methods']:
        target=method.get('url') or method['address'];title=method['title']
        link=f'[{title}]({target})' if method.get('url') else f'{title} · {method["network"]}: `{target}`'
        copy=payload['texts']['en']
        lines.append(f'| {link} | {copy["method_cadence_"+method["cadence"]]} | {copy["method_status_"+method["status"]]} |')
    lines+=['',payload['texts']['en']['support_provider_note'],'','<details>','<summary>QR codes for your phone</summary>','']
    for method in payload['methods']:
        if method['qr']:
            digest=hashlib.sha256((ROOT/'website/assets/support'/(method['id']+'.svg')).read_bytes()).hexdigest()[:12]
            lines += [f'<p>{html.escape(method["title"])}</p>',f'<img src="website/assets/support/{method["id"]}.svg?v={digest}" alt="Scan {html.escape(method["title"])}" width="180" height="180">','']
    lines+=['</details>','']
    lines.append(payload['texts']['en']['support_note'])
    if payload['supporters']:
        lines+=['','#### Supporters','']+[f'- {html.escape(s["name"])} · {html.escape(s["since"])}' for s in payload['supporters']]
    lines.append(end);block='\n'.join(lines)
    if begin in text:text=text[:text.index(begin)]+block+text[text.index(end)+len(end):]
    else:text=text.replace('### Source and credits',block+'\n\n### Source and credits')
    readme.write_text(text)
    subprocess.run([sys.executable,str(ROOT/'scripts/generate-guides.py')],check=True)
    funding=''
    for method_id,key in (('kofi','ko_fi'),('patreon','patreon')):
        method=next((m for m in payload['methods'] if m['id']==method_id),None)
        if method:funding+=key+': '+method['url'].rstrip('/').split('/')[-1]+'\n'
    (ROOT/'.github/FUNDING.yml').write_text(funding)
    print('Support generated:',len(payload['methods']),'enabled methods;',len(payload['supporters']),'supporters')


if __name__=='__main__':main()
