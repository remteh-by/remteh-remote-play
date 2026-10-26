# Deckivo — installation and play guide

Deckivo **0.8.3 preview** · 2026-10-25

[English](en.md) · [Русский](ru.md) · [Українська](uk.md) · [Polski](pl.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [Português](pt.md) · [Türkçe](tr.md) · [简体中文](zh.md) · [日本語](ja.md) · [한국어](ko.md) · [العربية](ar.md) · [हिन्दी](hi.md) · [Bahasa Indonesia](id.md)

## Before you start

Deckivo 0.8.3 is an experimental open-source PS5 Remote Play client. Start on the same home network. On PS5, select the profile you intend to use, then Settings → System → Remote Play → Enable Remote Play. Keep the console awake during first pairing. A 5 GHz Wi-Fi connection is preferable; a guest network may isolate devices. This client does not install Android/Linux or modify PS5 firmware.

<a id="android"></a>

## Android

### First installation

1. Download the arm64 APK linked below; Android 8+ is required. Install it and allow installation only for the chosen source when prompted. Keep Play Protect enabled.
2. Open Deckivo, choose the language and pair with the PS5 profile you want to use. Pair a compatible gamepad in Android Bluetooth settings.

### Update

1. Keep automatic updates enabled. Allow Deckivo to install from this source when Android asks; confirm the system installer. Android may require this confirmation for each update.
2. For manual recovery, install the same-signer APK over Deckivo. Do not uninstall or clear storage: console pairing, settings and language are retained.

### Uninstall

1. End the stream, then use Android Settings → Apps → Deckivo → Uninstall. This removes the app and its private pairing/settings/history on this device.
2. APK files or reports saved in Downloads remain; remove those separately if unwanted. PS5 games and saves are not removed. A later reinstall needs pairing again.

[Android APK](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.3/Deckivo-0.8.3-arm64.apk) · [Release / SHA-256](https://github.com/remteh-by/remteh-remote-play/releases/tag/v0.8.3)

<a id="macos"></a>

## macOS

### First installation

1. Use an Apple Silicon Mac with macOS 13+. Install the official chiaki-ng app separately and register the PS5 there. Close its stream.
2. Extract the Mac ZIP and move Deckivo.app into ~/Applications. This preview is ad-hoc signed, not notarized. After an attempted launch, use the individual Open Anyway option in System Settings → Privacy & Security if macOS requires it. Do not disable Gatekeeper globally.
3. Open Deckivo Preferences, import your chiaki-ng registration and select the console address. Keep chiaki-ng installed: Deckivo uses its native engine.

### Update

1. Leave automatic updates enabled; installation waits until streaming ends. Registration and settings remain in ~/Library/Application Support/Deckivo/private.
2. For a manual update, quit Deckivo and replace only Deckivo.app with the extracted app. Keep the data directory and chiaki-ng.

### Uninstall

1. Quit Deckivo and move Deckivo.app from ~/Applications (or your chosen install location) to Trash. This does not remove chiaki-ng or Deckivo data.
2. To remove saved registration, settings, history and downloaded updates too, remove ~/Library/Application Support/Deckivo in Finder only after backing up anything you need. It contains private pairing credentials; never share it.
3. chiaki-ng is a separate application with separate data. Remove it separately only if no longer wanted. PS5 games and saves remain on the console.

[Mac ZIP · 0.8.3 b19](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.3/Deckivo-macos-0.8.3-b19.zip) · [chiaki-ng](https://github.com/streetpea/chiaki-ng/releases)

<a id="ubuntu"></a>

## Switchroot Ubuntu

### First installation

1. Use the supported Switchroot Ubuntu 24.04 ARM64 environment and its matching drivers. Install the dependencies listed in docs/LINUX.md; download the complete source kit and extract it. The small update ZIP is insufficient for first installation.
2. From the extracted root run python3 desktop/linux/build-install.py, then python3 desktop/linux/pair.py. Follow private pairing prompts and open Deckivo from Applications. Do not replace the Switchroot NVIDIA/FFmpeg drivers.

### Update

1. Keep automatic updates enabled. The user timer stages signed packages; the GUI applies them while idle. Pairing and settings are retained.
2. For manual recovery extract the Linux update ZIP and run python3 desktop/linux/upgrade.py from its root. An existing runtime is required.

### Uninstall

1. Close Deckivo. Disable the timers and remove their unit files with the commands below, before removing the installed runtime.
2. Remove ~/.local/bin/deckivo, ~/.local/share/applications/Deckivo.desktop and the Deckivo.desktop shortcut in your desktop folder. Removing ~/.local/share/deckivo also removes the runtime and Linux registration.json. Back up that private file first if you want to retain pairing.
3. Settings, update cache and history in ~/.config/deckivo remain until separately removed. Keep them if wanted; they may contain credentials. Games and saves on PS5 are unaffected.

```sh
systemctl --user disable --now deckivo-update.timer deckivo-update-login.timer
systemctl --user stop deckivo-update.service
rm -f ~/.config/systemd/user/deckivo-update.timer ~/.config/systemd/user/deckivo-update-login.timer ~/.config/systemd/user/deckivo-update.service
systemctl --user daemon-reload
```

```sh
# Initial runtime (complete source kit)
python3 desktop/linux/build-install.py
# Interactive pairing
python3 desktop/linux/pair.py
# Upgrade an existing runtime only
python3 desktop/linux/upgrade.py
```

[Linux update ZIP · 0.8.3 b19](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.3/Deckivo-Linux-0.8.3-b19-source.zip) · [Linux requirements](../LINUX.md) · [Complete source kit](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.3/Deckivo-0.8.3-sources.zip)

## Pairing and first connection

Use the Account ID of the selected PS5 profile in Base64 form, not its nickname or email. Android accepts it in the wizard. The optional local PS5 helper can read it only on a console already capable of running the supplied ELF; it is not needed for ordinary Remote Play. Next open PS5 Settings → System → Remote Play → Link Device and enter the fresh eight-digit code before it expires. The helper code and Remote Play code are different. On Linux the interactive script reads credentials privately; on Mac import your own chiaki-ng registration. Never share registration files, PINs or keys.

## Controls and quality

Start at 720p and lower bitrate/30 FPS if Wi-Fi is unstable. These are requested settings, not measured performance promises. GameSir G8+ was tested on Android in blue mode and in Ubuntu with its controller adapter. On Android swipe up briefly from the bottom edge to show the hidden PS/Touch controls. On Linux Home maps to PS and Capture to the touchpad; the +/− disconnect chord is optional. Verify both sticks, triggers, buttons and sound on your device. Save the game before ending a stream; disconnecting does not close the game.

## Automatic updates

Keep the same package/signing identity and install over the previous version. Android checks public GitHub releases while the home/update screen is open, normally every six hours, and can download on unmetered Wi-Fi. Android 12+ may install a self-update after source permission; Android can still require confirmation. Mac/Linux use signed metadata and verified hashes, wait for an idle stream, then restart the app. A sleeping device or closed app is not a permanent background updater. Older private-channel builds need a one-time transition; see the update guide.

[Update details](../UPDATES.md)

## Troubleshooting and limits

If pairing fails, check the profile, Account ID, fresh PIN, console IP and network isolation. For a black screen, end the stream, close other Remote Play clients and reconnect; try lower quality. For failed updates, use the release APK/package over the existing installation and retain app data. See the exact device/build matrix below. Internet/VPN play, wake-from-rest, every controller function and sustained sessions are not certified. Windows, Intel Mac and desktop Linux x64 are planned. WebKit/jailbreak hangs belong to the console and are not fixed by this client.

[Device / version / scope](../TESTED.md) · [Technical reference](../TECHNICAL.md)

<!-- SUPPORT:START -->
## Help Deckivo grow

Deckivo is free and open source. Your support helps fund signing, new platforms and real-device testing.

- Apple Developer ID ($99/yr) — signing and notarization for Mac
- Windows build
- More test hardware: PS5 Pro and handhelds

[Ko-fi · RemTeh](https://ko-fi.com/pavelzayats)

<img src="../../website/assets/support/kofi.svg" width="180" height="180" alt="Scan with your phone">

Everything stays free. Supporting is optional.
<!-- SUPPORT:END -->
