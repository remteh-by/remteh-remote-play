#!/usr/bin/env python3
"""Publish locally signed previews to the owner's private LAN feed."""
import argparse,base64,hashlib,json,os,plistlib,re,shutil,stat,subprocess,sys,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PRIVATE=Path.home()/'.codex/private/deckivo-updates'

def entry(path,platform,version,build,**extra):
 return {'platform':platform,'version':version,'build':build,'filename':path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),**extra}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--desktop-build',type=int,required=True);parser.add_argument('--mac-app',type=Path,default=Path.home()/'Applications/Deckivo.app');group=parser.add_mutually_exclusive_group();group.add_argument('--only-linux',action='store_true');group.add_argument('--only-android',action='store_true');args=parser.parse_args()
 os.umask(0o077);config=json.loads((PRIVATE/'channel.json').read_text());dest=Path(config['directory']);dest.mkdir(exist_ok=True)
 sys.path.insert(0,str(ROOT/'desktop/linux'))
 from session import VERSION
 from upgrade import FILES
 packages=[]
 if args.only_linux:packages=[row for row in json.loads((dest/'index.json').read_text())['packages'] if row['platform']!='linux-switch-arm64']
 if args.only_android:packages=[row for row in json.loads((dest/'index.json').read_text())['packages'] if row['platform']!='android-arm64']
 app=args.mac_app
 if app.exists() and not args.only_linux and not args.only_android:
  with tempfile.TemporaryDirectory(prefix='deckivo-publish-') as name:
   staged=Path(name)/'Deckivo.app';shutil.copytree(app,staged,symlinks=True)
   info=plistlib.loads((staged/'Contents/Info.plist').read_bytes())
   if info['CFBundleShortVersionString']!=VERSION or args.desktop_build<=int(info['CFBundleVersion']):raise ValueError('Desktop update must be newer than the installed bootstrap')
   info['CFBundleVersion']=str(args.desktop_build);(staged/'Contents/Info.plist').write_bytes(plistlib.dumps(info))
   subprocess.run(['/usr/bin/codesign','--force','--deep','--sign','-',str(staged)],check=True,capture_output=True)
   file=dest/f'Deckivo-macos-{VERSION}-b{args.desktop_build}.zip'
   with zipfile.ZipFile(file,'w',zipfile.ZIP_DEFLATED) as archive:
    for directory,dirs,files in os.walk(staged,followlinks=False):
     for leaf in sorted(dirs+files):
      path=Path(directory)/leaf;relative=str(path.relative_to(staged.parent))
      if path.is_symlink():
       item=zipfile.ZipInfo(relative);item.external_attr=(stat.S_IFLNK|0o777)<<16;archive.writestr(item,os.readlink(path))
      elif path.is_file():archive.write(path,relative)
  packages.append(entry(file,'macos-arm64',VERSION,args.desktop_build))
 apk=ROOT/f'dist/Deckivo-{VERSION}-arm64.apk'
 if apk.exists() and not args.only_linux:
  sdk=Path.home()/'Library/Android/sdk/build-tools/36.0.0/aapt2'
  badging=subprocess.run([str(sdk),'dump','badging',str(apk)],check=True,capture_output=True,text=True).stdout
  android=int(re.search(r"versionCode='(\d+)'",badging).group(1));version=re.search(r"versionName='([^']+)'",badging).group(1)
  if version!=VERSION:raise ValueError('Android artifact and desktop version differ')
  file=dest/f'Deckivo-{version}-b{android}-arm64.apk';shutil.copy2(apk,file)
  packages.append(entry(file,'android-arm64',version,android,minSdk=26,packageName='by.remteh.remoteplay',abi='arm64-v8a'))
 if not args.only_android:
  file=dest/f'Deckivo-Linux-{VERSION}-b{args.desktop_build}-source.zip'
  with zipfile.ZipFile(file,'w',zipfile.ZIP_DEFLATED) as archive:
   for name in FILES:
    path=ROOT/'desktop/linux'/name
    if name=='build_meta.py':archive.writestr('desktop/linux/'+name,'BUILD = '+str(args.desktop_build)+'\n')
    else:archive.write(path,'desktop/linux/'+name)
  shutil.copy2(file,ROOT/'dist'/file.name)
  packages.append(entry(file,'linux-switch-arm64',VERSION,args.desktop_build))
 index=json.dumps({'schema':1,'packages':packages},separators=(',',':'),sort_keys=True).encode()
 temp=dest/'index.new';temp.write_bytes(index)
 signature=subprocess.run(['/usr/bin/openssl','dgst','-sha256','-sign',str(PRIVATE/'signing.pem'),str(temp)],check=True,capture_output=True).stdout
 (dest/'index.sig').write_bytes(base64.b64encode(signature));temp.replace(dest/'index.json')
 print('Private signed feed:',[(e['platform'],e['version'],e['build']) for e in packages])
if __name__=='__main__':main()
