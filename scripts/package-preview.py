#!/usr/bin/env python3
"""Package a local preview and exact source checkout without publishing an OTA feed."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apk', type=Path, required=True)
    parser.add_argument('--mac-app', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT).strip():
        raise SystemExit('Commit the preview sources before recording their exact revision.')
    version = re.search(r'versionName "([0-9.]+)"', (ROOT/'android/app/build.gradle').read_text())[1]
    prefix = 'Deckivo-'+version
    output = args.output.resolve()
    if output.exists():
        raise SystemExit('Use a new empty output directory; previous preview artifacts are retained.')
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    files = [Path(name) for name in tracked if name and (ROOT/name).is_file()]
    forbidden = {'.jks', '.keystore', '.apk', '.idsig', '.pyc'}
    files = [p for p in files if p.suffix not in forbidden and p.name not in ('.env', 'password.txt', 'local.properties')]
    bases = list((ROOT/'android/app/.cxx').glob('*/*/arm64-v8a/_deps'))
    dependencies = ('mbedtls', 'json-c', 'miniupnpc')
    dep_base = next((p for p in bases if all((p/(d+'-src')).is_dir() for d in dependencies)), None)
    if dep_base is None:
        raise SystemExit('Native dependency sources are required; build Android first.')
    output.mkdir(parents=True)
    shutil.copy2(args.apk, output/(prefix+'-arm64.apk'))
    subprocess.run(['/usr/bin/ditto', '-c', '-k', '--sequesterRsrc', '--keepParent',
                    str(args.mac_app), str(output/(prefix+'-macos-arm64.zip'))], check=True)
    with zipfile.ZipFile(output/(prefix+'-sources.zip'), 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            archive.write(ROOT/path, 'source/'+path.as_posix())
        for dep in dependencies:
            base = dep_base/(dep+'-src')
            for folder, dirs, names in os.walk(base):
                dirs[:] = sorted(d for d in dirs if d not in ('.git', 'build', '__pycache__'))
                for name in sorted(names):
                    path = Path(folder)/name
                    if path.name in ('.git', '.DS_Store') or path.suffix == '.pyc':
                        continue
                    archive.write(path, 'source/vendor/'+dep+'/'+path.relative_to(base).as_posix())
    with zipfile.ZipFile(output/(prefix+'-linux-preview.zip'), 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            if (path.as_posix().startswith(('desktop/linux/', 'localization/', 'LICENSES/', 'docs/'))
                    or path.name in ('COPYING', 'ATTRIBUTION.md', 'UPSTREAM-LOCK.json')):
                archive.write(ROOT/path, prefix+'-linux/'+path.as_posix())
    shutil.copy2(ROOT/'dist'/(prefix+'-desktop.cdx.json'), output/(prefix+'-desktop.cdx.json'))
    shutil.copy2(ROOT/'docs/releases'/(version+'-development-validation.json'), output/'verification.json')
    shutil.copy2(ROOT/'docs/CONTROLLERS.md', output/'CONTROLLERS.md')
    shutil.copy2(ROOT/'docs/releases'/(version+'-development.md'), output/'README.md')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    (output/'SOURCE-REVISION.json').write_text(json.dumps({'version': version, 'git_revision': revision,
        'channel': 'local preview', 'public_update_feed_written': False}, indent=2)+'\n')
    for path in output.glob('*.zip'):
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise SystemExit('Archive integrity failure: '+path.name)
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file()}
    (output/'SHA256SUMS.txt').write_text(''.join(f'{digest}  {name}\n' for name, digest in hashes.items()))
    print(json.dumps({'output': str(output), 'revision': revision, 'files': len(hashes), 'published': False}, indent=2))


if __name__ == '__main__':
    main()
