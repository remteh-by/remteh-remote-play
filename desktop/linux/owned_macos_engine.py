"""A private app-owned engine copy for the optional SDL adapter.

The official installation is read-only. No change to system security controls.
The engine remains a separately installed dependency, so old update clients do
not need to download a 400 MB engine in the Deckivo application package.
"""
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import uuid


def prepare(source, bridge, private, controller_backend=None):
    source,bridge,private=Path(source),Path(bridge),Path(private)
    if not source.is_file() or not bridge.is_file():
        raise RuntimeError('The installed chiaki-ng engine or Deckivo input adapter is missing.')
    identity={'engine_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'bridge_sha256':hashlib.sha256(bridge.read_bytes()).hexdigest()}
    backend=Path(controller_backend) if controller_backend else bridge.with_name('libSDL2.dylib')
    if not backend.is_file():raise RuntimeError('The genuine SDL2 controller backend is missing.')
    identity['controller_backend_sha256']=hashlib.sha256(backend.read_bytes()).hexdigest()
    key=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()[:20]
    root=private/'owned-engines';root.mkdir(parents=True,exist_ok=True);root.chmod(0o700)
    target=root/key/'Deckivo Engine.app'
    receipt=target.parent/'ready.json'
    if receipt.is_file() and json.loads(receipt.read_text())==identity and (target/'Contents/MacOS/chiaki').is_file():
        return target/'Contents/MacOS/chiaki'
    if shutil.disk_usage(root).free<1200*1024**2:
        raise RuntimeError('Keep 1.2 GB free for the private streaming engine copy.')
    stage=root/('.building-'+uuid.uuid4().hex)
    try:
        bundle=stage/'Deckivo Engine.app'
        shutil.copytree(source.parents[2],bundle,symlinks=True)
        # The vendor bundle ships an SDL2-compat/SDL3 shim. Use the app's pinned
        # genuine SDL2 ABI in our private copy so virtual input has one backend.
        sdl=bundle/'Contents/Frameworks/libSDL2-2.0.0.dylib'
        sdl.unlink(missing_ok=True);shutil.copy2(backend,sdl)
        subprocess.run(['install_name_tool','-id','@rpath/libSDL2-2.0.0.dylib',str(sdl)],check=True,capture_output=True)
        info=bundle/'Contents/Info.plist';metadata=plistlib.loads(info.read_bytes())
        metadata.update(CFBundleIdentifier='by.remteh.deckivo.engine',CFBundleName='Deckivo Engine',CFBundleDisplayName='Deckivo Engine')
        info.write_bytes(plistlib.dumps(metadata))
        subprocess.run(['codesign','--force','--deep','--options','0','--sign','-',str(bundle)],check=True,capture_output=True)
        subprocess.run(['codesign','--verify','--deep','--strict',str(bundle)],check=True,capture_output=True)
        (stage/'ready.json').write_text(json.dumps(identity));(stage/'ready.json').chmod(0o600)
        # A caller holds the stream lock; incomplete destinations are never used.
        if target.parent.exists():shutil.rmtree(target.parent)
        stage.rename(target.parent)
    finally:
        if stage.exists():shutil.rmtree(stage)
    return target/'Contents/MacOS/chiaki'
