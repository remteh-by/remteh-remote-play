#!/usr/bin/env python3
"""Build/install this Mac's private native Deckivo app, preserving private data."""
import argparse,json,os,platform,plistlib,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DATA=Path.home()/'Library/Application Support/Deckivo'
PRIVATE=DATA/'private'
RUNTIME=DATA/'python'

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--build',type=int,default=10);parser.add_argument('--stage-only',action='store_true');parser.add_argument('--private-preview',action='store_true');parser.add_argument('--output-dir',type=Path);parser.add_argument('--no-install-deps',action='store_true');args=parser.parse_args()
 if sys.platform!='darwin' or platform.machine()!='arm64':raise SystemExit('This package targets the current Apple Silicon Mac.')
 os.umask(0o077)
 if not args.stage_only:PRIVATE.mkdir(parents=True,exist_ok=True);PRIVATE.chmod(0o700)
 if not (RUNTIME/'bin/python').exists():
  subprocess.run([sys.executable,'-m','venv',str(RUNTIME)],check=True)
 if not args.no_install_deps:subprocess.run([str(RUNTIME/'bin/python'),'-m','pip','install','--disable-pip-version-check','-r',str(ROOT/'desktop/macos/requirements.txt')],check=True)
 subprocess.run([str(RUNTIME/'bin/python'),'-c','import PyInstaller'],check=True)
 shared=ROOT/'desktop/linux';sys.path.insert(0,str(shared))
 from session import VERSION
 package=args.output_dir or DATA/'packaging';package.mkdir(parents=True,exist_ok=True)
 iconset=package/'Deckivo.iconset';iconset.mkdir(exist_ok=True)
 render='''from PyQt5.QtWidgets import QApplication\nfrom PyQt5.QtGui import QPainter,QImage\nfrom PyQt5.QtSvg import QSvgRenderer\nfrom pathlib import Path\nimport sys\napp=QApplication([]);svg=QSvgRenderer(sys.argv[1]);out=Path(sys.argv[2])\nfor size in (16,32,128,256,512):\n for scale in (1,2):\n  image=QImage(size*scale,size*scale,QImage.Format_ARGB32);image.fill(0);p=QPainter(image);svg.render(p);p.end();image.save(str(out/('icon_%dx%d%s.png'%(size,size,'@2x' if scale==2 else ''))))\n'''
 subprocess.run([str(RUNTIME/'bin/python'),'-c',render,str(shared/'deckivo.svg'),str(iconset)],env={**os.environ,'QT_QPA_PLATFORM':'offscreen'},check=True)
 icon=package/'Deckivo.icns'
 subprocess.run(['iconutil','-c','icns',str(iconset),'-o',str(icon)],check=True)
 command=[str(RUNTIME/'bin/python'),'-m','PyInstaller','--noconfirm','--clean','--windowed',
     '--name','Deckivo','--osx-bundle-identifier','by.remteh.deckivo','--icon',str(icon),
     '--distpath',str(package/'frozen'),'--workpath',str(package/'work'),'--specpath',str(package),
     '--paths',str(shared),'--add-data',str(shared/'assets')+':assets',
     '--add-binary','/opt/homebrew/opt/sdl2/lib/libSDL2.dylib:assets/macos',
     '--add-data','/opt/homebrew/opt/sdl2/LICENSE.txt:licenses/SDL2',
     '--add-data',str(shared/'deckivo.svg')+':.','--add-data',str(ROOT/'LICENSES')+':licenses']
 # The external helper runtime needs real source files after the GUI is frozen.
 for path in shared.glob('*.py'):command+=['--add-data',str(path)+':.']
 subprocess.run(command+[str(shared/'macos_main.py')],check=True)
 stage=package/'frozen/Deckivo.app';info_path=stage/'Contents/Info.plist'
 info=plistlib.loads(info_path.read_bytes())
 info.update({'CFBundleDisplayName':'Deckivo','CFBundleShortVersionString':VERSION,'CFBundleVersion':str(args.build),
     'LSMinimumSystemVersion':'13.0','NSHighResolutionCapable':True,
     'NSLocalNetworkUsageDescription':'Deckivo connects to your PS5 and retrieves signed local updates.'})
 info_path.write_bytes(plistlib.dumps(info))
 subprocess.run(['/usr/bin/codesign','--force','--deep','--sign','-',str(stage)],check=True)
 subprocess.run(['/usr/bin/codesign','--verify','--deep','--strict',str(stage)],check=True)
 if args.stage_only:
  print('Staged:',stage);return
 destination=Path.home()/'Applications/Deckivo.app';destination.parent.mkdir(exist_ok=True)
 if destination.exists():
  old=plistlib.loads((destination/'Contents/Info.plist').read_bytes())
  if old.get('CFBundleIdentifier')!='by.remteh.deckivo':raise SystemExit('Destination belongs to another application.')
  backup=PRIVATE/'rollback'/str(time.time_ns())/'Deckivo.app';backup.parent.mkdir(parents=True);destination.rename(backup)
 shutil.copytree(stage,destination,symlinks=True)
 channel={'base_url':'https://remteh-by.github.io/remteh-remote-play/updates/'}
 if args.private_preview:
  channel={'base_url':json.loads((Path.home()/'.codex/private/deckivo-updates/channel.json').read_text())['base_url'],'private_preview':True}
 (PRIVATE/'update-channel.json').write_text(json.dumps(channel));(PRIVATE/'update-channel.json').chmod(0o600)
 desktop=Path.home()/'Desktop/Deckivo.app'
 if not desktop.exists():desktop.symlink_to(destination)
 print('Installed:',destination)
 print('Pairing/preferences retained; source and update signing key are outside the app bundle.')
if __name__=='__main__':main()
