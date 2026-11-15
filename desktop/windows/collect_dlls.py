"""Collect the DLLs referenced by the deployed executable, Qt plugins and QML modules."""
import re
import shutil
import subprocess
import sys
from collections import deque
from pathlib import Path

stage, prefix = map(Path, sys.argv[1:])
binary_dir = prefix / "bin"
available = {p.name.lower(): p for p in binary_dir.glob("*.dll")}
pending = deque(p for p in stage.rglob("*") if p.suffix.lower() in {".exe", ".dll"})
analyzed = set()
while pending:
    binary = pending.popleft()
    if binary in analyzed:
        continue
    analyzed.add(binary)
    headers = subprocess.check_output([binary_dir / "objdump.exe", "-p", binary])
    for entry in re.findall(rb"DLL Name:\s*([^\r\n]+)", headers):
        name = entry.decode("ascii").strip().lower()
        source = available.get(name)
        if source and not (stage / source.name).exists():
            pending.append(Path(shutil.copy2(source, stage)))
print(f"Inspected {len(analyzed)} executable images")
