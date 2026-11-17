#!/usr/bin/env python3
"""Verify the site's release registry against GitHub before deploying its buttons."""
import hashlib,json,os,re,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def group_assets(document):
 groups={}
 for asset in document['assets']:
  name=asset.get('name','');url=asset.get('url','')
  match=re.fullmatch(r'https://github[.]com/remteh-by/remteh-remote-play/releases/download/(v[0-9]+[.][0-9]+[.][0-9]+)/([A-Za-z0-9][A-Za-z0-9._-]*)',url)
  if not match or match[2]!=name or not re.fullmatch(r'[a-f0-9]{64}',asset.get('sha256','')):
   raise ValueError('Invalid published asset binding: '+name)
  if isinstance(asset.get('bytes'),bool) or not isinstance(asset.get('bytes'),int) or asset['bytes']<=0:
   raise ValueError('Invalid asset size: '+name)
  rows=groups.setdefault(match[1],[])
  if any(row['name']==name for row in rows):raise ValueError('Duplicate release asset: '+name)
  rows.append(asset)
 required={str(document['version']),str(document.get('desktop_version',document['version']))}
 if any('v'+version not in groups for version in required):raise ValueError('Published platform release has no assets')
 return groups

def main():
 document=json.loads((ROOT/'website/published-release.json').read_text())
 headers={'Accept':'application/vnd.github+json','User-Agent':'Deckivo-release-check'}
 if os.environ.get('GITHUB_TOKEN'):headers['Authorization']='Bearer '+os.environ['GITHUB_TOKEN']
 verified=0
 for tag,expected_assets in group_assets(document).items():
  url='https://api.github.com/repos/remteh-by/remteh-remote-play/releases/tags/'+tag
  with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=30) as response:release=json.load(response)
  if release.get('draft') or release.get('prerelease')!=(document['channel']=='preview'):raise SystemExit('Release state mismatch: '+tag)
  assets={row['name']:row for row in release['assets']}
  for expected in expected_assets:
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
   verified+=1
 print('Verified published platform releases and',verified,'assets')
if __name__=='__main__':main()
