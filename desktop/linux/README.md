# Deckivo for Switchroot Ubuntu

Experimental Linux preview **0.6.0** for the owner's Switch OLED running
Switchroot Ubuntu 24.04.4 ARM64. This is a native Python/Qt interface with an
isolated native Chiaki 2.2.0 streaming engine and Deckivo's Tegra/input adapter.
It is not an Android APK. Public 0.6.0 sources/upgrade pack are experimental; the exact physical evidence below remains versioned.

## Run

Open **Deckivo** on the Switch desktop or application menu. Choose a streaming
profile and press **Let's play / Начать игру**. Console registration is kept
locally. Home maps to PS; Switch Capture maps to the touchpad click. The native
engine's Ctrl+Q shortcut ends a stream. Hold **+ and − together for 1.5 seconds**
to disconnect without a keyboard. Disable this chord in Preferences if needed.
Closing the stream leaves PS5 running.

## What's included in 0.5.1

- Shared design assets with Android and macOS.
- Pinned-signature private updates: check, download and idle installation.
- Background workers finish before app shutdown; an active stream defers updates.
- On 25 October the physical Switch upgraded from build 6 to build 7 through
  this updater and restarted, retaining pairing, preferences and session history.

- A graphite, lime and violet native dashboard with an official PS5 product image.
- Four screens: Play space, Controller lab, Sessions and Preferences.
- Gamepad navigation in Deckivo: D-pad/stick, positional A/B, L1/R1 for pages.
- Live stick/button visualisation through Linux's read-only joystick interface.
- A temporary connecting sheet that disappears only after a decoded video frame.
- Decoder frame count and observed decoder FPS; these are not rendered FPS.
- PS5 discovery-response timing, separately labelled from video/input latency.
- Graceful disconnect from the dashboard, tray, private local command or gamepad
  chord. The native engine is asked to quit through its own Qt event loop.
- Private session history (up to 40 rows) and an allowlisted diagnostic export
  without IP addresses, accounts, pairing keys or raw logs.
- Preserved local pairing, English/default and automatic/system language.
  New Linux features are translated into English and Russian; other languages
  currently use English for these strings.

The adapter and original four-screen UI were compiled/rendered on the physical
Switch. Version 0.5.1 is now installed and its updater is device-verified.
New stream/chord behaviour still requires gameplay acceptance. The earlier 0.3
video/audio/input acceptance below applies to the retained engine and does not
certify every new frontend feature.

## Upgrade an existing Switch installation

Close Deckivo and its stream, extract the complete source kit and run:

```sh
python3 desktop/linux/upgrade.py
```

This builds the new adapter with the installed matching headers, keeps a
versioned rollback copy, and retains pairing/preferences. It does not download
packages or change system drivers. To roll back, close Deckivo and restore the
files from the printed `~/.local/share/deckivo-backups/before-0.5.1-*` folder.
The initial installation remains available through `build-install.py` below.

## Design handoff

`design/01-play-space.svg` through `04-preferences.svg` are editable screens
with separate text layers and an embedded original Sony product image. Import them into Figma.
The Figma file was created, but canvas editing is currently blocked by its
Starter MCP limit. See `design/figma-handoff.json` for the file and exact status.
These SVGs are reference screens, not live connection or performance evidence.
The product image is retained without geometric changes; its source and SHA-256
are recorded in `assets/source.json`. Image credits are in `assets/NOTICE.txt`.

The preview supports local play. An Internet/VPN route is a separate task and
has not been validated. WebKit is not required for the Remote Play connection;
launching modified games on PS5 remains a separate console-side operation.

## Verified and pending

- Native interface rendered on the physical Switch, including automatic Russian
  locale and the language picker. Shared Deckivo language catalogs are included;
  Linux-specific text currently has English and Russian translations.
- Pairing with the owner's selected profile succeeded using the PS5 device PIN.
- Live 1280×720 frames were decoded by `h264_nvv4l2`. The preset asks for 60 FPS;
  this does not certify sustained 60 FPS during gameplay.
- The adapter supplies dimensions before opening Switchroot's Tegra decoder,
  preventing the observed `Picture size 0x0 is invalid` failure.
- SDL opened the connected Pro Controller device. Exclusive controller capture
  was confirmed by a successful EVIOCGRAB on SDL's own evdev descriptor.
- An independent lock test confirmed rejection of a second streaming process
  and release of the lock after exit.
- **25 October acceptance:** after a normal PS5 restart the owner confirmed
  picture, sound and GameSir input. Nonzero PCM audio at the Switch's speaker
  output was independently observed. Remote Play was then closed with Ctrl+Q
  while WebKit loaded its programs, and reconnected after Payload Manager
  reported 8/8 successful with zero failures. This reconnect needed no further
  PS5 restart. Sustained gameplay remains an acceptance gate; earlier retries
  did encounter PS5 session-busy and control-channel errors.
- chiaki-ng 1.10.0 ARM64 was downloaded with its published SHA-256 and tested
  separately in OpenGL mode. It is an experimental candidate, not this
  preview's default engine. Do not run it alongside Deckivo.

## Build / reinstall

On this same Switchroot Ubuntu installation, run:

```sh
python3 desktop/linux/build-install.py
```

Requires the existing Python/PyQt5, GCC, OpenSSL development headers, KDE/X11,
SDL2 and Switchroot FFmpeg 6.1 (`libavcodec.so.60`). The installer downloads
Ubuntu packages through apt, extracts them into the current user's directory,
verifies the upstream source checksum, and compiles the two native adapters.
It does not use sudo or replace the system decoder/driver packages.

This installer targets the already configured device. Initial pairing currently
uses `native/deckivo-register`: host, the profile's Base64 account ID and a fresh
8-digit PS5 PIN are supplied on stdin, with the output filename as the only
argument. Never put those values into shell arguments, logs, the repository or
the source kit. Registration keys must be written only to a private local file.

## Storage / privacy

Application and isolated runtime: `~/.local/share/deckivo/`.
Preferences and private engine settings: `~/.config/deckivo/`.
Pairing: `~/.local/share/deckivo/registration.json`, mode 0600 inside a private
directory. Keep it out of copies of the source code. The same applies to session
logs and the Chiaki engine's per-user log directory.

The frontend uses a private Unix socket for its local launcher command and a
lock for the entire stream lifetime. It opens no network service. Console
availability uses the PS5 UDP discovery protocol, not connections to its Remote
Play TCP control port. Discovery is limited to the configured host.

## Credits

Developed by [RemTeh.by](https://remteh.by), using the work of Chiaki and
Switchroot/FFmpeg. Preserve their authorship and licenses. This preview and the
underlying engine remain subject to the repository's AGPL/OpenSSL licensing
terms. Public 0.x versions are experimental prereleases; see the current [platform guide](../../docs/guides/en.md#ubuntu) and test matrix.
