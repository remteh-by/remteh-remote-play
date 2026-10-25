# Switchroot Ubuntu ARM64 technical setup

This is a developer preview for an already prepared **Switch OLED**,
**Switchroot Ubuntu 24.04 ARM64**, **KDE/X11**, and Switchroot **FFmpeg 6.1
(`libavcodec.so.60`)**. It is not a universal Linux installer or an OS installer.
Back up your own data before changing your OS; Deckivo does not repartition it.

## Prerequisites

Python 3 with PyQt5, GCC, OpenSSL development headers, SDL2, apt/dpkg-deb and
working Switchroot audio/input/decoder drivers. `build-install.py` checks OS,
architecture, PyQt5, compiler and FFmpeg before continuing. It downloads pinned
Ubuntu packages into the user's isolated runtime with apt and validates the
Chiaki 2.2.0 source SHA-256 before compiling its adapters. It does not use sudo,
upgrade the OS or replace NVIDIA/FFmpeg drivers. Pinned packages may become
unavailable in Ubuntu mirrors: stop rather than silently substituting versions.
A clean installation on another Switch has not been accepted.

## Initial installation

Extract the complete release source archive and open its `source/` directory.
Do not use the small upgrade ZIP for a first installation.

```sh
python3 desktop/linux/build-install.py
python3 desktop/linux/pair.py
```

The pairing script prompts for your PS5 IPv4, the selected profile's Base64
Account ID and a fresh 8-digit PS5 Remote Play code. Account ID and PIN are not
command-line arguments or printed logs. A failed pairing retains the previous
registration. If already registered, the previous file is retained locally.
Open Deckivo from the applications menu; choose a streaming preset and play.

## Existing installation

Close the stream and Deckivo, extract the upgrade ZIP, then run from its root:

```sh
python3 desktop/linux/upgrade.py
```

Runtime, registration and preferences are retained. Existing matching headers
and GCC are required. The printed private backup directory supports rollback.
There is no reason to reformat a card, delete saves or activate another profile
for a client update.

## Private storage and controls

`~/.local/share/deckivo/` contains runtime and registration; `~/.config/deckivo/`
contains preferences/history/engine settings. Treat registration files as keys;
keep them out of public source uploads. Home maps to PS, Capture to touchpad.
Ctrl+Q closes the native stream. The optional +/− hold chord and new controller
lab must be checked on your device. The engine isolates controller capture to
its stream, rather than globally injecting keyboard events.

[Device results](TESTED.md) · [Local setup guides](guides/en.md)
