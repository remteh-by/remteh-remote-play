#!/usr/bin/env python3
"""Bootstrap the signed updater on the owner's existing Switchroot installation.

Uses an existing authenticated SSH access module, never stores its keys, and
refuses to change files while the existing client reports an active stream.
"""
import argparse
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from updater import check_and_download

REMOTE = r'''
import base64,hashlib,json,os,signal,socket,subprocess,sys,tempfile,time,zipfile,io
from pathlib import Path
os.umask(0o077)
request=json.load(sys.stdin)
raw=base64.b64decode(request['archive'],validate=True)
if hashlib.sha256(raw).hexdigest()!=request['sha256']:raise SystemExit('Transfer verification failed')
data=Path.home()/'.local/share/deckivo';private=Path.home()/'.config/deckivo'
if not (data/'runtime/usr/bin/chiaki').exists():raise SystemExit('Existing Deckivo runtime was not found')
registration=data/'registration.json'
before=hashlib.sha256(registration.read_bytes()).hexdigest() if registration.exists() else None
def command(value):
 with socket.socket(socket.AF_UNIX) as client:
  client.settimeout(2);client.connect(str(private/'launcher.sock'));client.sendall(value.encode())
  return json.loads(client.recv(65536))
try:state=command('status')
except OSError:state=None
if state and state.get('running'):raise SystemExit('End the Remote Play stream before updating')
pids=[]
for path in Path('/proc').iterdir():
 if not path.name.isdigit() or int(path.name)==os.getpid():continue
 try:args=(path/'cmdline').read_bytes().split(b'\0')
 except OSError:continue
 if len(args)>1 and args[1] in (str(data/'deckivo.py').encode(),str(data/'launcher.py').encode()):pids.append(int(path.name))
if pids:
 if state is None:raise SystemExit('Cannot confirm that Deckivo is idle; close it first')
 try:accepted=command('quit').get('accepted',False)
 except OSError:accepted=False
 if not accepted:
  for pid in pids:
   try:os.kill(pid,signal.SIGTERM)
   except ProcessLookupError:pass
 for _ in range(40):
  if not any(Path('/proc',str(pid)).exists() for pid in pids):break
  time.sleep(.1)
 else:raise SystemExit('Deckivo is still closing; no files changed')
with tempfile.TemporaryDirectory(prefix='deckivo-bootstrap-') as directory:
 root=Path(directory)
 with zipfile.ZipFile(io.BytesIO(raw)) as archive:
  for entry in archive.infolist():
   path=Path(entry.filename)
   if path.is_absolute() or '..' in path.parts:raise SystemExit('Unsafe source package')
  archive.extractall(root)
 subprocess.run([sys.executable,str(root/'desktop/linux/upgrade.py')],check=True)
private.mkdir(parents=True,exist_ok=True);private.chmod(0o700)
channel=private/'update-channel.json';channel.write_text(json.dumps({'base_url':request['base_url']}));channel.chmod(0o600)
if before is not None and before!=hashlib.sha256(registration.read_bytes()).hexdigest():raise SystemExit('Registration retention check failed')
environment={**os.environ,'DISPLAY':':0','XDG_RUNTIME_DIR':'/run/user/'+str(os.getuid()),'DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/'+str(os.getuid())+'/bus'}
with (private/'launcher-private.log').open('ab') as log:
 subprocess.Popen([str(Path.home()/'.local/bin/deckivo')],env=environment,stdout=log,stderr=log,start_new_session=True)
for _ in range(60):
 try:
  state=command('status')
  if state.get('version')==request['version'] and state.get('build')==request['build']:
   print(json.dumps({'version':state['version'],'build':state['build'],'pairing_retained':True,'updater_configured':True}));break
 except (OSError,ValueError):pass
 time.sleep(.25)
else:raise SystemExit('Files installed; GUI startup needs checking on the Switch')
'''


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--access',type=Path,required=True,help='Existing owner SSH access module')
    args=parser.parse_args();os.umask(0o077)
    spec=importlib.util.spec_from_file_location('switch_access',args.access)
    access=importlib.util.module_from_spec(spec);spec.loader.exec_module(access)
    host=access.select_host()
    private=Path.home()/'.codex/private/deckivo-updates'
    channel=json.loads((private/'channel.json').read_text())
    update=check_and_download(channel['base_url'],'linux-switch-arm64','0.0.0',0,
        private/'bootstrap-cache',Path(__file__).resolve().parent/'assets/update-public.der')
    if update is None:raise SystemExit('No compatible signed Linux update')
    entry=update['entry'];raw=Path(update['file']).read_bytes()
    request={'archive':base64.b64encode(raw).decode(),'sha256':entry['sha256'],
        'base_url':channel['base_url'],'version':entry['version'],'build':entry['build']}
    result=subprocess.run(access.SSH+['switch@'+host,'python3 -c '+shlex.quote(REMOTE)],input=json.dumps(request).encode())
    return result.returncode


if __name__=='__main__':
    try:sys.exit(main())
    except (RuntimeError,OSError) as error:raise SystemExit(str(error))
