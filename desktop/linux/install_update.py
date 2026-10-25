"""Verify and stage an update, wait for Deckivo to exit, then replace safely."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import zipfile
import uuid
from updater import verify_signature,candidate
from storage import HERE,PRIVATE,private_json,load_json

STARTUP_TIMEOUT=120


def wait_for_ack(transaction,process,timeout=STARTUP_TIMEOUT):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        acknowledgement=load_json(PRIVATE/'update-ack.json',{})
        if acknowledgement.get('transaction')==transaction and acknowledgement.get('pid')==process.pid:return True
        if process.poll() is not None:return False
        time.sleep(.25)
    return False


def stop_updated_process(process):
    if process.poll() is not None:return
    process.terminate()
    try:process.wait(timeout=10)
    except subprocess.TimeoutExpired as error:
        # Keep both copies intact rather than rename files under a live app.
        raise RuntimeError('Updated process is still running; rollback deferred safely') from error


def confirm_or_rollback(entry,transaction,process,restore,restart):
    if wait_for_ack(transaction,process):return
    stop_updated_process(process)
    restore()
    private_json(PRIVATE/'update-failed.json',{'sha256':entry['sha256'],'build':entry['build']})
    restart()
    raise ValueError('Updated app did not confirm startup; previous version restored')


def extract(archive,directory):
    directory=directory.resolve();root=directory;links=[];seen=set()
    with zipfile.ZipFile(archive) as source:
        entries=source.infolist()
        if len(entries)>5000 or sum(e.file_size for e in entries)>512*1024*1024:raise ValueError('Archive exceeds extraction limits')
        for entry in entries:
            path=Path(entry.filename)
            if path.is_absolute() or '..' in path.parts or '\\' in entry.filename or not path.parts or path in seen:raise ValueError('Unsafe archive path')
            seen.add(path)
            target=directory/path
            if stat.S_ISLNK(entry.external_attr>>16):
                link=source.read(entry).decode('utf-8')
                if not link or Path(link).is_absolute() or '\\' in link:raise ValueError('Unsafe symbolic link')
                links.append((target,link));continue
            if entry.is_dir():target.mkdir(parents=True,exist_ok=True);continue
            target.parent.mkdir(parents=True,exist_ok=True)
            with source.open(entry) as src,target.open('wb') as dest:shutil.copyfileobj(src,dest)
            target.chmod(0o755 if entry.external_attr>>16 & 0o111 else 0o644)
        # Native framework aliases must be relative and remain in the staging tree.
        for target,link in links:
            try:
                target.parent.resolve().relative_to(root)
                Path(os.path.normpath(target.parent/link)).relative_to(root)
            except (ValueError,RuntimeError):raise ValueError('Symbolic link escapes the update')
            target.parent.mkdir(parents=True,exist_ok=True)
            target.symlink_to(link)
        for target,link in links:
            try:target.resolve().relative_to(root)
            except (ValueError,RuntimeError):raise ValueError('Symbolic link escapes the update')


def main(descriptor,parent):
    os.umask(0o077)
    update=json.loads(Path(descriptor).read_text());entry=update['entry'];archive=Path(update['file'])
    payload=Path(update['index']).read_bytes();signature=Path(update['signature']).read_bytes()
    verify_signature(payload,signature,HERE/'assets/update-public.der')
    if entry not in json.loads(payload)['packages']:raise ValueError('Package is outside signed index')
    if archive.stat().st_size!=entry['bytes'] or hashlib.sha256(archive.read_bytes()).hexdigest()!=entry['sha256']:raise ValueError('Package verification failed')
    staging=Path(tempfile.mkdtemp(prefix='deckivo-stage-',dir=PRIVATE))
    extract(archive,staging)
    for _ in range(120):
        try:os.kill(int(parent),0)
        except ProcessLookupError:break
        time.sleep(.25)
    else:raise ValueError('Deckivo did not exit; no files changed')
    transaction=uuid.uuid4().hex
    receipt={'version':entry['version'],'build':entry['build'],'sha256':entry['sha256'],'transaction':transaction,'state':'installed','time':time.time()}
    if entry['platform']=='macos-arm64':
        import plistlib
        app=staging/'Deckivo.app';info=plistlib.loads((app/'Contents/Info.plist').read_bytes())
        if info.get('CFBundleIdentifier')!='by.remteh.deckivo' or info.get('CFBundleShortVersionString')!=entry['version'] or int(info.get('CFBundleVersion',0))!=entry['build']:raise ValueError('Wrong application bundle')
        installed=Path.home()/'Applications/Deckivo.app'
        current=plistlib.loads((installed/'Contents/Info.plist').read_bytes())
        if candidate({'schema':1,'packages':[entry]},entry['platform'],current['CFBundleShortVersionString'],int(current['CFBundleVersion'])) is None:raise ValueError('Update is already installed or older')
        subprocess.run(['/usr/bin/codesign','--verify','--deep','--strict',str(app)],check=True,capture_output=True)
        backup=PRIVATE/'rollback'/str(time.time_ns())/'Deckivo.app';backup.parent.mkdir(parents=True,exist_ok=True)
        installed.rename(backup)
        try:app.rename(installed)
        except BaseException:backup.rename(installed);raise
        private_json(PRIVATE/'update-receipt.json',receipt)
        def launch_mac():
            return subprocess.Popen([str(installed/'Contents/MacOS/Deckivo')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
        def restore_mac():
            installed.rename(staging/'failed.app');backup.rename(installed)
        process=launch_mac()
        confirm_or_rollback(entry,transaction,process,restore_mac,launch_mac)
    elif entry['platform']=='linux-switch-arm64':
        from session import VERSION
        from build_meta import BUILD
        if candidate({'schema':1,'packages':[entry]},entry['platform'],VERSION,BUILD) is None:raise ValueError('Update is already installed or older')
        result=subprocess.run([sys.executable,str(staging/'desktop/linux/upgrade.py'),'--json'],check=True,capture_output=True,text=True)
        backup=Path(json.loads(result.stdout)['backup'])
        from upgrade import restore_backup
        def launch_linux():
            return subprocess.Popen([str(Path.home()/'.local/bin/deckivo')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
        private_json(PRIVATE/'update-receipt.json',receipt)
        process=launch_linux()
        confirm_or_rollback(entry,transaction,process,lambda:restore_backup(backup),launch_linux)
    else:raise ValueError('Wrong target platform')
    private_json(PRIVATE/'update-receipt.json',receipt);(PRIVATE/'update-error.json').unlink(missing_ok=True);shutil.rmtree(staging)


if __name__=='__main__':
    try:main(sys.argv[1],sys.argv[2])
    except Exception as error:
        (PRIVATE/'update-error.json').write_text(json.dumps({'state':'failed','error':str(error)}))
        raise
