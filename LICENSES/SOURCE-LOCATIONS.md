# Bundled desktop components

Deckivo's complete project source and build scripts accompany the release.
Dependencies retain their licenses; the binary bundle does not prevent replacing
the corresponding shared libraries. No Developer ID restriction or device key is
needed to build this open-source preview.

- PyQt5 5.15.11: Riverbank, GPL v3. Source distribution and files:
  https://pypi.org/project/PyQt5/5.15.11/#files
- Qt 5.15.19 (PyQt5-Qt5 wheel): LGPL v3 components; original license notice is
  included. Qt's corresponding open-source tag is `v5.15.19-lts-lgpl`:
  https://code.qt.io/cgit/qt/qtbase.git/tag/?h=v5.15.19-lts-lgpl
  and https://code.qt.io/cgit/qt/qtsvg.git/tag/?h=v5.15.19-lts-lgpl
  (The Qt 5.15.19 open-source release announcement lists the source repositories:
  https://lists.qt-project.org/pipermail/announce/2026-May/000626.html.)
- PyQt5-sip 12.20.0: https://pypi.org/project/PyQt5-sip/12.20.0/#files
- PyInstaller 6.22.3: GPL v2 with its bootloader exception; included notice.
  https://github.com/pyinstaller/pyinstaller/tree/v6.22.3
- truststore 0.10.5: MIT; included notice.
  https://github.com/sethmlarson/truststore/tree/v0.10.5
- CPython: the exact Python version and original LICENSE are included in the
  packaged app's notices; https://www.python.org/downloads/source/
- SDL2: zlib license, included with the packaged library. Source and build:
  https://github.com/libsdl-org/SDL/tree/SDL2
- IBM Plex Sans: the bundled font's OFL.txt is included alongside the font.

Mac streaming uses a separately installed chiaki-ng app; its own source, notices
and distribution remain with that application. Linux installation validates the
original Chiaki archive and downloads system packages into an isolated runtime.
