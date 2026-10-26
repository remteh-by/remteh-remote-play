# Deckivo 0.8.3 platform scope

| Target | Delivery | Exact-device evidence |
|---|---|---|
| Android ARM64 | 0.8.3 build 28 APK; Android 8+ minimum | Switch OLED / Android 15: earlier public 0.6.1 build 25; new-build acceptance is separate |
| macOS Apple Silicon | 0.8.3 build 19; macOS 13+; separately installed official chiaki-ng | MacBook / macOS 27.0.1: public 0.8.2 build 18 updater and Donate passed; latest transition recorded separately |
| Switchroot Ubuntu ARM64 | 0.8.3 build 19 upgrade/source pack; prepared Ubuntu 24.04.4, KDE X11, FFmpeg 6.1 | Switch OLED public 0.8.1 build 17 updater, reboot and Wi-Fi passed; later packages are not automatically hardware acceptance |
| Windows x64 | Planned | No verified Deckivo package |
| Intel Mac | Planned | No verified Deckivo package |
| Desktop Linux x64 | Planned | No verified Deckivo package |
| Other OSes | Research | No delivery claim |

Android retains the C/Kotlin Remote Play engine. Mac uses a separately installed chiaki-ng 1.10.0 engine through an owned private copy. Switchroot Ubuntu uses an isolated Chiaki 2.2.0 runtime with Tegra/input adapters. Branding and catalogs are shared; executables and capabilities differ.

Local play does not require a permanent home PC or a Deckivo account. External Internet/VPN access and waking the console require separate network and exact-device verification. Maximum supported requested profile is 1080p; 4K streaming is not implemented.

See [actual test results](TESTED.md), [updates](UPDATES.md) and [current setup guides](guides/en.md).
