# Deckivo — installation and play guide

Deckivo **0.6.1 preview** · 2026-10-25

[English](en.md) · [Русский](ru.md) · [Українська](uk.md) · [Polski](pl.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [Português](pt.md) · [Türkçe](tr.md) · [简体中文](zh.md) · [日本語](ja.md) · [한국어](ko.md) · [العربية](ar.md) · [हिन्दी](hi.md) · [Bahasa Indonesia](id.md)

## Before you start

Deckivo 0.6.1 is an experimental open-source PS5 Remote Play client. Start on the same home network. On PS5, select the profile you intend to use, then Settings → System → Remote Play → Enable Remote Play. Keep the console awake during first pairing. A 5 GHz Wi-Fi connection is preferable; a guest network may isolate devices. This client does not install Android/Linux or modify PS5 firmware.

## Android

Download the arm64 APK from the release linked below. Android 8 or newer is required; physical testing used Android 15 on Switch OLED. Allow installation for your chosen browser/file manager only when Android asks. Install over an existing Deckivo installation: do not uninstall or clear data. Open Deckivo, choose a language and use the connection wizard. Connect your Bluetooth gamepad in Android settings. Never disable Play Protect for this app.

[Android APK](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.6.1/Deckivo-0.6.1-arm64.apk) · [Release / SHA-256](https://github.com/remteh-by/remteh-remote-play/releases/tag/v0.6.1)

<a id="macos"></a>

## macOS

Apple Silicon only in this preview. Install the official chiaki-ng Mac application separately, register your PS5 there and close its stream. Download and extract Deckivo-macos-0.6.1-b10.zip, then move Deckivo.app to ~/Applications. The bundle is ad-hoc signed and is not notarized: macOS may require a deliberate Open Anyway action in System Settings → Privacy & Security after an attempted launch. Do not disable Gatekeeper globally. In Deckivo Preferences choose the pairing/import action, select the existing chiaki-ng registration and enter your console address. Keep chiaki-ng installed: Deckivo uses its native engine.

[Mac ZIP · 0.6.1 b10](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.6.1/Deckivo-macos-0.6.1-b10.zip) · [chiaki-ng](https://github.com/streetpea/chiaki-ng/releases)

<a id="ubuntu"></a>

## Switchroot Ubuntu

Switchroot Ubuntu 24.04 ARM64 with KDE/X11 and matching Switchroot FFmpeg 6.1 is the developer target. A new device needs the complete source kit, PyQt5, GCC, OpenSSL/SDL2 development dependencies and the initial runtime installer. Run the initial command below from the extracted source root, then run the interactive pairing command. The small Linux upgrade ZIP is only for an already installed runtime. Do not replace NVIDIA/FFmpeg drivers to force compatibility. If a pinned apt package is unavailable, stop and keep the working installation.

```sh
# Initial runtime (complete source kit)
python3 desktop/linux/build-install.py
# Interactive pairing
python3 desktop/linux/pair.py
# Upgrade an existing runtime only
python3 desktop/linux/upgrade.py
```

[Linux requirements](../LINUX.md) · [Complete source kit](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.6.1/Deckivo-0.6.1-sources.zip)

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
