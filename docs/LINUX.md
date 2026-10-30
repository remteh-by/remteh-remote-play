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
python3 desktop/linux/preflight.py
python3 desktop/linux/build-install.py
python3 desktop/linux/pair.py
```

The pairing script prompts for your PS5 IPv4, the selected profile's Base64
Account ID and a fresh 8-digit PS5 Remote Play code. Account ID and PIN are not
command-line arguments or printed logs. A failed pairing retains the previous
registration. If already registered, the previous file is retained locally.
Open Deckivo from the applications menu; choose a streaming preset and play.

The 0.8.7 build 23 source candidate adds a read-only preflight report for architecture, Ubuntu version, Python, KDE/X11, FFmpeg ABI, SDL2/OpenSSL, build tools, free space, write access and an existing runtime. A failed check stops before installation. Mirror availability is checked by apt during the actual first install; preflight does not promise that downloads will succeed.

## Existing installation

With automatic updates enabled, existing public-channel clients receive Linux
0.8.6 build 22 from GitHub. Leave Deckivo on its idle dashboard with Internet
access. After this update, a user timer can download later signed updates while
Deckivo is closed; installation waits for its next idle launch. Ubuntu must be
awake and the user logged in. No Mac-based update server is required.

For a manual recovery only:

Close the stream and Deckivo, extract the upgrade ZIP, then run from its root:

```sh
python3 desktop/linux/upgrade.py
```

Runtime, registration and preferences are retained. Existing matching headers
and GCC are required. The printed private backup directory supports rollback.
There is no reason to reformat a card, delete saves or activate another profile
for a client update.

The hourly user timer is `deckivo-update.timer`; check it with
`systemctl --user status deckivo-update.timer`. It respects Deckivo's automatic
updates setting. A failed check retries later instead of disabling updates.
Wi-Fi credentials belong to Ubuntu/NetworkManager and are never included in
Deckivo's release packages or changed by its updater.

## Private storage and controls

`~/.local/share/deckivo/` contains runtime and registration; `~/.config/deckivo/`
contains preferences/history/engine settings. Treat registration files as keys;
keep them out of public source uploads. Home maps to PS, Capture to touchpad.
Ctrl+Q closes the native stream. The optional +/− hold chord and new controller
lab must be checked on your device. The engine isolates controller capture to
its stream, rather than globally injecting keyboard events.

[Device results](TESTED.md) · [Local setup guides](guides/en.md)

Since 0.8.3, deckivo-update-login.timer performs the initial check about 45 seconds after user login, and deckivo-update.timer checks every 60 minutes with up to 10 minutes randomized delay. Updates migrate the old two-minute unit automatically. Both timers are disabled by turning off automatic updates.
