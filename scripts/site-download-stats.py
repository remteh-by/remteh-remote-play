#!/usr/bin/env python3
"""Best-effort statistics: unavailable API data must never block Pages delivery."""
import argparse
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
UNAVAILABLE = {'schema': 1, 'available': False}


def collect(output, command=None, timeout=90):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    reason = None
    with tempfile.TemporaryDirectory(dir=output.parent) as directory:
        staged = Path(directory) / 'statistics.json'
        try:
            args = command or [sys.executable, str(ROOT / 'scripts/download-stats.py')]
            result = subprocess.run([*args, '--output', str(staged)], capture_output=True, timeout=timeout)
            if result.returncode:
                raise ValueError(f'collector exit {result.returncode}')
            if not 0 < staged.stat().st_size <= 10 * 1024 * 1024:
                raise ValueError('empty or oversized statistics')
            validate = runpy.run_path(str(ROOT / 'scripts/build-site.py'))['load_download_stats']
            if validate(staged) is None:
                raise ValueError('collector reported unavailable statistics')
        except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
            reason = type(error).__name__
            staged.write_text(json.dumps(UNAVAILABLE) + '\n')
        staged.replace(output)
    if reason:
        message = 'Download statistics unavailable; publishing the site and update channel without counters.'
        print(f'::warning::{message} ({reason})')
        summary = os.environ.get('GITHUB_STEP_SUMMARY')
        if summary:
            with open(summary, 'a') as stream:
                stream.write(f'\n### Download statistics\n\n⚠️ {message}\n')
    return reason is None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    collect(args.output)
