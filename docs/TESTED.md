# Device and version test matrix

Last evidence review: **2026-10-25**. “Installed”, “updater passed” and “gameplay
accepted” are separate results. Requested resolution/FPS are not measured FPS.
No personal registration files, account identifiers or raw device logs are public.

| Platform / hardware | Software | Verified on that exact configuration | Still open |
|---|---|---|---|
| Apple Silicon MacBook, macOS 27.0.1 | Deckivo 0.8.0 #16 → 0.8.2 #18 | Public signed auto-update, all 415 installed ZIP entries match, codesign verified, startup acknowledged, pairing retained; native donation button opens the correct RemTeh Ko-fi page and app stays alive | Sustained gameplay/controller acceptance; Android/Ubuntu 0.8.2 physical tests are separate |
| Switch OLED, Android 15 / API 35, ARM64 | Deckivo 0.5.1 #18 → #19 → #20 | Native PackageInstaller self-update, same package/certificate, installer identified as Deckivo itself; original install timestamp and encrypted-data directory retained; app returned to dashboard with saved console | Sustained gameplay and every controller function in the redesigned frontend |
| Apple Silicon MacBook, macOS 27.0.1 | Deckivo 0.5.1 #3 → #4 → #5 | Signed updater, bundle verification, replacement/relaunch, startup acknowledgment, registration hash unchanged; no new Deckivo/Python crash report during this check | Sustained new-frontend play/controller acceptance; Developer ID/notarization |
| Switch OLED, Switchroot Ubuntu 24.04.4 ARM64, KDE/X11 | Deckivo 0.6.1 #10 → 0.8.1 #17 | Signed public update installed and relaunched; all 80 installer files match the public package; matching receipt/startup acknowledgment and live version readback; registration retained; exact timer units enabled and natural closed-app background checks reported current before and after a full Ubuntu reboot; Wi-Fi autoconnected with KWallet closed | Sustained redesigned-frontend gameplay/controller acceptance |
| Switch OLED / Android 15 / GameSir G8+ blue mode | Earlier 0.1.x client, 0.1.2 quick controls | Owner confirmed PS5 picture, menu audio and basic GameSir control; PS/Touch panel behaviour tested | Complete analog-trigger/controller matrix and long sessions |
| Switch OLED / Ubuntu / GameSir G8+ | Earlier 0.3.0 engine path; Chiaki 2.2.0 | Owner confirmed picture, sound and control; 1280×720 decoded frames via h264_nvv4l2, nonzero speaker PCM, exclusive controller capture, reconnect after console autoload | Sustained 60 FPS is not certified; newer frontend does not inherit full acceptance |
| Apple Silicon MacBook | chiaki-ng 1.10.0 native engine | Owner confirmed PS5 picture and sound before the shared frontend update | Full Deckivo 0.6.0 gameplay/controller acceptance |

## Console reference

The connected PS5 advertised **system-version `13420000` (13.42)** in a fresh
read-only Remote Play discovery response on 2026-10-25. The owner identifies it
as a non-Slim, third hardware revision; the exact model label was not read for
this release. Historical sessions did not capture a separate full firmware
string every time. No other firmware/model compatibility range is certified.

## 0.6.0 public-channel verification

- **Mac 0.6.0 build 8 → build 9:** the installed app fetched RSA-signed metadata
  from public GitHub Pages and its ZIP from GitHub Releases, installed itself,
  relaunched, acknowledged startup and reported up to date. The registration hash
  stayed unchanged. This is updater acceptance, not sustained gameplay.
- **Android 0.6.0 build 23 → build 24:** found/downloaded the public GitHub
  release, verified size/SHA-256/package/version/certificate, completed the
  normal Play Protect scan and installed through Deckivo itself. The installed
  base APK hash equals the published APK exactly. First-install time and the
  saved console card were retained. No uninstall/data clear was used.
- Ubuntu is currently offline while the same Switch runs Android. The public
  0.6.0 Linux pack is prepared; its physical proof stays at 0.5.1 build 7.

[Public-channel proof](releases/0.6.0-public-channel-validation.json) records the
actual results after publication; the original release validation remains intact.

## 0.6.0 release checks

The release validation JSON records Android release build/lint/unit tests, native
unit tests, signature/size/identity checks and website checks. Public-channel and
physical results are added only after the actual transition is observed. A row
above is not silently relabelled “0.6.0 tested” because the same engine is reused.

Android installer prompts, Play Protect checks and source-install permissions are
normal platform controls. Play Protect was left enabled; the owner explicitly
approved its scan during the earlier physical update test.

## Not certified

Internet/VPN play from an external network; waking the PS5 from rest; every
button/analog trigger on every controller; sustained latency/FPS and long sessions;
Windows, Intel Mac or desktop Linux x64. Android 8 is the declared minimum, not a
claim of testing on an Android 8 device. macOS 13 is the package minimum, not a
claim of testing every macOS release. No Android/Linux installation on a blank
Switch, firmware update, jailbreak reliability or game compatibility certification.

[Guide languages](guides/en.md) · [Update behaviour](UPDATES.md)

## 0.6.1 public-channel verification

- Android 0.6.0 #24 → 0.6.1 #25: exact public APK, same certificate, self-installer, original install date and saved console retained. Russian support, local QR and offline licenses opened. Actual PS5 video received after closing duplicate test clients; normal disconnect worked. Audio/controller and sustained play still require owner acceptance on this build.
- Mac 0.6.0 #9 → 0.6.1 #10: RSA public update, matching startup acknowledgment, registration hash retained, Russian support QR decoded. External-engine video was seen, but two engine instances made ownership ambiguous. Normal stop left an external engine alive; isolated stream/stop acceptance remains open for the next version.
- Ubuntu 0.6.1 #10: package and rollback tests passed; hardware remains at the previously verified version while the same Switch runs Android.
- All twelve v0.6.0 asset IDs, names, sizes and digests still match the pre-work snapshot.

[0.6.1 physical receipt](releases/0.6.1-public-channel-validation.json).

## 0.7.0 local development preview

- MacBook Apple Silicon / macOS 27.0.1: build 14 installed locally with a rollback
  bundle and unchanged registration hash. The owned streaming child decoded 210
  actual PS5 frames. A normal window close stopped the session and returned to idle
  in 0.69 seconds. Earlier build 13 exposed a shutdown ordering bug; its result is
  not relabelled as a pass. This is a short stream/stop check, not sustained play.
- The final native SDL adapter passed a standalone input probe: button, left stick,
  trigger and timeout neutralization. No game input was sent to the console by it.
- Android 0.7.0 #26 is built and signed with the existing certificate, but has not
  been installed on the Switch. Ubuntu remains at its last physical test version.
- 37 Android release unit tests and 46 desktop tests passed. Android Lint reports
  no new findings with 96 upstream baseline warnings. Controller lab EN/RU layouts
  passed 12 width cases from 390 to 3840 px without horizontal overflow. Controller
  photographs have equal body height and no artificial floor shadow.
- Physical Sony USB calibration, controller-specific motors/sensors/audio,
  keyboard/mouse aiming in a game, sustained 1080p and Internet play remain open.
  4K is not exposed because the retained Remote Play engine supports up to 1080p.
- Existing signed update verification remains intact. No 0.7.0 tag, public release
  or update feed has been published; this local preview is not a new OTA test.

[Development receipt](releases/0.7.0-development-validation.json) ·
[Controller features and input guide](CONTROLLERS.md).

## 0.8.1 Linux packaging checks

- Physical Switch OLED / Ubuntu 24.04.4 ARM64 / KDE/X11 was found running
  0.6.1 build 10, with automatic updates enabled and the public feed still
  offering build 10. The installed upgrade helper was missing.
- Both updated native adapters compiled on that device with GCC and strict
  warnings. A private device-side backup of registration/preferences was made.
- 74 desktop/package tests passed. The signed Linux upgrade has 94 unique paths
  including license documents; the macOS feed entry remains unchanged.
- Physical public-channel 0.6.1 build 10 → 0.8.1 build 17 is verified on the
  actual Switch OLED. All 80 installed files match the public package; its
  install receipt, startup acknowledgment and live version agree, and the
  registration was retained.
- The exact packaged user service/timer units are enabled. After the GUI closed,
  the next natural timer run completed successfully and reported 0.8.1 build 17
  current, with no warning/error journal entries.
- Full Ubuntu reboot, Wi-Fi autoconnection with KWallet closed and another
  natural background update check passed. Gameplay/controller acceptance remains
  separate and was not performed on this build.

[0.8.1 public-channel readback](releases/0.8.1-public-channel-validation.json)
records the verified public download and exact-device update acceptance. It does
not certify gameplay or controller behaviour.

The same Ubuntu device was subsequently fully rebooted: its saved Wi-Fi profile
autoconnected while KWallet remained closed, and the Deckivo timer checked the
public channel again. The Wi-Fi change is owner-device configuration, not a
feature that modifies networks in the distributed application.

## 0.8.2 public update and donation verification

The installed Mac updated from 0.8.0 build 16 to 0.8.2 build 18 using the public
signed feed and release ZIP. All 415 installed entries matched, the startup
acknowledgment belonged to the live process, and pairing was retained. The
native support dialog and its donation button were clicked after installation:
Chrome loaded **Support RemTeh** at `https://ko-fi.com/pavelzayats`, while
Deckivo stayed alive. No payment was submitted.

The shared Mac/Ubuntu callback regression is covered by actual Qt button-click
tests. Android uses a separate Kotlin browser/QR path. Physical Android and
Ubuntu 0.8.2 tests remain pending because the Switch was unavailable.

[Public acceptance receipt](releases/0.8.2-public-channel-validation.json).
