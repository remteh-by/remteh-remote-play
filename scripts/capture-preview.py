#!/usr/bin/env python3
"""Capture a real Deckivo Qt window with isolated, empty private storage."""
import argparse
import hashlib
import importlib
import json
import os
from datetime import datetime,timezone
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
ROOT=Path(__file__).resolve().parents[1]


def file_hash(path):
 digest=hashlib.sha256()
 with path.open('rb') as source:
  for chunk in iter(lambda:source.read(1024*1024),b''):digest.update(chunk)
 return digest.hexdigest()


def ui_sources(source_root):
 desktop=source_root/'desktop/linux';paths=sorted(desktop.glob('*.py'))
 for relative in ('assets/fonts/IBMPlexSans.ttf','assets/ps5-console.png','assets/source.json'):
  path=desktop/relative
  if path.is_file():paths.append(path)
 return sorted(set(paths))


def source_hash(source_root,paths):
 digest=hashlib.sha256()
 for path in paths:
  relative=path.relative_to(source_root).as_posix().encode();digest.update(len(relative).to_bytes(4,'big'));digest.update(relative)
  with path.open('rb') as source:
   for chunk in iter(lambda:source.read(1024*1024),b''):digest.update(chunk)
 return digest.hexdigest()


def git_value(source_root,*arguments):
 result=subprocess.run(('git','-C',str(source_root),*arguments),check=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 return result.stdout.strip()


def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--source-root',type=Path,default=ROOT,help='Deckivo source checkout whose real Qt UI is rendered')
 parser.add_argument('--output',type=Path,default=ROOT/'build/deckivo-ui.png',help='capture PNG destination')
 parser.add_argument('--metadata',type=Path,default=ROOT/'build/deckivo-ui.capture.json',help='capture metadata destination')
 args=parser.parse_args();source_root=args.source_root.expanduser().resolve();desktop=source_root/'desktop/linux'
 required=(desktop/'launcher.py',desktop/'session.py',desktop/'build_meta.py',desktop/'assets/fonts/IBMPlexSans.ttf')
 missing=[str(path) for path in required if not path.is_file()]
 if missing:raise SystemExit('Invalid Deckivo source root; missing: '+', '.join(missing))
 args.output.parent.mkdir(parents=True,exist_ok=True);args.metadata.parent.mkdir(parents=True,exist_ok=True)
 sys.path.insert(0,str(desktop))
 from PyQt5.QtGui import QFontDatabase
 from PyQt5.QtWidgets import QApplication
 launcher=importlib.import_module('launcher');controller=importlib.import_module('controller');storage=importlib.import_module('storage');update_ui=importlib.import_module('update_ui');support=importlib.import_module('support')
 app=QApplication.instance() or QApplication([]);app.setStyleSheet(launcher.STYLE);QFontDatabase.addApplicationFont(str(desktop/'assets/fonts/IBMPlexSans.ttf'))
 with tempfile.TemporaryDirectory(prefix='deckivo-capture-') as directory:
  isolated=Path(directory);data=isolated/'data';private=isolated/'private';config=private/'preferences.json';engine=private/'engine/Chiaki/Chiaki.conf'
  patches=(patch.object(launcher,'DATA',data),patch.object(launcher,'PRIVATE',private),patch.object(launcher,'CONFIG',config),patch.object(storage,'DATA',data),patch.object(storage,'PRIVATE',private),patch.object(storage,'CONFIG',config),patch.object(storage,'ENGINE_CONFIG',engine),patch.object(launcher.Deckivo,'refresh',lambda self:None),patch.object(launcher,'ControllerMonitor',controller.ControllerMonitor),patch.object(update_ui,'initialize',lambda self:None),patch.object(support,'maybe_thank',lambda self:None))
  with patches[0],patches[1],patches[2],patches[3],patches[4],patches[5],patches[6],patches[7],patches[8],patches[9],patches[10]:
   window=launcher.Deckivo();window.resize(1280,720);window.show();app.processEvents();pixmap=window.grab()
   if pixmap.isNull() or not pixmap.save(str(args.output),'PNG'):raise RuntimeError('Qt window capture failed')
   window.close();app.processEvents()
 paths=ui_sources(source_root);commit=git_value(source_root,'rev-parse','HEAD');dirty=bool(git_value(source_root,'status','--porcelain','--untracked-files=no'))
 metadata={'schema':1,'version':str(launcher.VERSION),'build':int(launcher.BUILD),'source_commit':commit,'source_dirty':dirty,'ui_source_sha256':source_hash(source_root,paths),'ui_source_files':[path.relative_to(source_root).as_posix() for path in paths],'capture_state':'unpaired','development_preview':True,'captured_at':datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'),'image':{'filename':args.output.name,'sha256':file_hash(args.output),'width':pixmap.width(),'height':pixmap.height()},'privacy':'Temporary empty DATA, PRIVATE and CONFIG; no registration, pairing keys, account, IP address or session history loaded.'}
 args.metadata.write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
 print(f"Captured real Deckivo {metadata['version']} b{metadata['build']} UI from {commit[:12]} at {args.output}")


if __name__=='__main__':main()
