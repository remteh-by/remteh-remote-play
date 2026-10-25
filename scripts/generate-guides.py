#!/usr/bin/env python3
"""Render all install guides from reviewed language and owner funding catalogs."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'desktop/linux'))
from session import VERSION
from build_meta import BUILD
catalog=json.loads((ROOT/'localization/guides.json').read_text());support=json.loads((ROOT/'website/support.json').read_text());repo='https://github.com/remteh-by/remteh-remote-play';release=f'{repo}/releases/tag/v{VERSION}';download=f'{repo}/releases/download/v{VERSION}/'
links=' · '.join(f'[{x["name"]}]({code}.md)' for code,x in catalog.items())
for code,copy in catalog.items():
 lines=['# '+copy['title'],'',f'Deckivo **{VERSION} preview** · 2026-10-25','',links,'']
 for i in range(8):
  if i in (2,3):lines += [f'<a id="{"macos" if i==2 else "ubuntu"}"></a>','']
  lines+=['## '+copy['heads'][i],'',copy['p'][i],'']
  if i==1:lines += [f'[Android APK]({download}Deckivo-{VERSION}-arm64.apk) · [Release / SHA-256]({release})','']
  if i==2:lines += [f'[Mac ZIP · {VERSION} b{BUILD}]({download}Deckivo-macos-{VERSION}-b{BUILD}.zip) · [chiaki-ng](https://github.com/streetpea/chiaki-ng/releases)','']
  if i==3:lines += ['```sh','# Initial runtime (complete source kit)','python3 desktop/linux/build-install.py','# Interactive pairing','python3 desktop/linux/pair.py','# Upgrade an existing runtime only','python3 desktop/linux/upgrade.py','```','',f'[Linux requirements](../LINUX.md) · [Complete source kit]({download}Deckivo-{VERSION}-sources.zip)','']
  if i==6:lines += ['[Update details](../UPDATES.md)','']
  if i==7:lines += ['[Device / version / scope](../TESTED.md) · [Technical reference](../TECHNICAL.md)','']
 text=support['texts'][code];lines += ['<!-- SUPPORT:START -->','## '+text['support'],'',text['support_body'],'']
 for goal in support['goals']:lines+=['- '+text[goal['title_key']]]
 lines+=['']
 for method in support['methods']:
  destination=method.get('url') or method['address'];lines += [f'[{method["title"]}]({destination})' if method.get('url') else f'{method["title"]} · {method["network"]}: `{destination}`','']
  if method['qr']:lines += [f'<img src="../../website/assets/support/{method["id"]}.svg" width="180" height="180" alt="{text["scan_phone"]}">','']
 lines += [text['support_note'],'<!-- SUPPORT:END -->','']
 (ROOT/f'docs/guides/{code}.md').write_text('\n'.join(lines))
print('Generated',len(catalog),'install guides with enabled support methods.')
