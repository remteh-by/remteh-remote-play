# Separate monotonic private distribution build, independent of SemVer.
import plistlib
from pathlib import Path
import sys

BUILD = 22
if sys.platform=='darwin' and getattr(sys,'frozen',False):
    BUILD = int(plistlib.loads((Path(sys.executable).parents[1]/'Info.plist').read_bytes())['CFBundleVersion'])
