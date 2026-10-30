#!/usr/bin/env python3
"""Verify the site's release registry against GitHub before deploying its buttons."""
import hashlib,json,os,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 document=json.loads((ROOT/'website/published-release.json').read_text())
 url='https://api.github.com/repos/remteh-by/remteh-remote-play/releases/tags/v'+document['version']
 headers={'Accept':'application/vnd.github+json','User-Agent':'Deckivo-release-check'}
 if os.environ.get('GITHUB_TOKEN'):headers['Authorization']='Bearer '+os.environ['GITHUB_TOKEN']
 with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=30) as response:release=json.load(response)
 if release.get('draft') or release.get('prerelease')!=(document['channel']=='preview'):raise SystemExit('Release state mismatch')
 assets={row['name']:row for row in release['assets']}
 for expected in document['assets']:
  row=assets.get(expected['name'])
  if not row or row['browser_download_url']!=expected['url'] or row['size']!=expected['bytes']:raise SystemExit('Asset metadata mismatch: '+expected['name'])
  digest=row.get('digest')
  if digest:
   if digest!='sha256:'+expected['sha256']:raise SystemExit('Asset digest mismatch: '+expected['name'])
  else:
   sha=hashlib.sha256();size=0
   with urllib.request.urlopen(expected['url'],timeout=60) as response:
    while data:=response.read(1024*1024):sha.update(data);size+=len(data)
   if size!=expected['bytes'] or sha.hexdigest()!=expected['sha256']:raise SystemExit('Asset bytes mismatch: '+expected['name'])
 print('Verified published release and',len(assets),'assets')
if __name__=='__main__':main()
