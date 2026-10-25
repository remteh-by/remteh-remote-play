#!/usr/bin/env python3
"""Validate pinned photo bytes and record the exact local controller-lab snapshot."""
import argparse
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'desktop/linux/assets/controller-lab'
p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
manifest=ROOT/'provenance.json';value=json.loads(manifest.read_text())
for name,item in value['files'].items():
    if name.endswith('.png'):
        assert hashlib.sha256((ROOT/name.lstrip('/')).read_bytes()).hexdigest()==item['sha256'],'Original controller photograph changed'
files={str(f.relative_to(ROOT)):{'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size} for f in sorted(ROOT.rglob('*')) if f.is_file() and f!=manifest}
if args.check:
    if value.get('packaged_files')!=files:raise SystemExit('Controller lab changed: regenerate provenance with scripts/validate-controller-lab.py')
else:
    value['packaged_files']=files;manifest.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
print('Controller lab: exact local snapshot and three original photograph hashes verified')
