#!/usr/bin/env python3
"""CycloneDX from installed distributions used by this Mac build runtime."""
import importlib.metadata as md
import json,platform,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'desktop/linux'))
from session import VERSION
components=[]
for name in ('PyQt5','PyQt5-Qt5','PyQt5-sip','truststore'):
 d=md.distribution(name);purl=f'pkg:pypi/{d.metadata["Name"].lower()}@{d.version}'
 components.append({'type':'library','name':d.metadata['Name'],'version':d.version,'bom-ref':purl,'purl':purl,'licenses':[{'expression':{'PyQt5':'GPL-3.0-only','PyQt5-Qt5':'LGPL-3.0-only','PyQt5-sip':'BSD-2-Clause','truststore':'MIT'}[name]}]})
components += [{'type':'platform','name':'CPython','version':platform.python_version(),'bom-ref':'runtime:cpython','licenses':[{'license':{'id':'Python-2.0'}}]}, {'type':'library','name':'SDL2','version':subprocess.check_output(['/opt/homebrew/opt/sdl2/bin/sdl2-config','--version'],text=True).strip(),'bom-ref':'runtime:sdl2','licenses':[{'license':{'id':'Zlib'}}]}]
bom={'bomFormat':'CycloneDX','specVersion':'1.6','version':1,'metadata':{'component':{'type':'application','name':'Deckivo desktop macOS','version':VERSION,'bom-ref':'deckivo:desktop','licenses':[{'expression':'LicenseRef-AGPL-3.0-only-OpenSSL'}]}},'components':components,'dependencies':[{'ref':'deckivo:desktop','dependsOn':[x['bom-ref'] for x in components]}]}
output=R/f'dist/Deckivo-{VERSION}-desktop.cdx.json';output.parent.mkdir(exist_ok=True);output.write_text(json.dumps(bom,indent=2)+'\n');print(output.name,len(components),'runtime components')
