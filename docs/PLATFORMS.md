# Deckivo platform scope

Public release: **0.8.7 preview**, Android build 32, desktop build 23. Published at the owner's request without physical-device acceptance. Mac packages use ad-hoc signing; no Developer ID notarization. Old release assets remain unchanged.

| Target | Candidate delivery | Acceptance boundary |
|---|---|---|
| Android ARM64 | 0.8.7 build 32; Android 8+ | Build, unit tests and lint; USB/Bluetooth, update over existing certificate, video/audio and lifecycle need physical device checks |
| macOS Apple Silicon | 0.8.7 build 23; macOS 13+; separate official chiaki-ng | Native tests and staged app; current PS5 gameplay, minimize/restore, input/background audio and sustained session pending |
| Switchroot Ubuntu ARM64 | 0.8.7 build 23 source/update candidate | Prepared Ubuntu 24.04, KDE/X11, Switchroot FFmpeg 6.1; actual installation, reboot and streaming pending |
| Windows, Intel Mac, desktop Linux x64 | No supported package | Planned/research, not a download promise |

Android uses the C/Kotlin engine; macOS uses a separately installed chiaki-ng through an owned private copy; Switchroot Ubuntu uses the isolated Chiaki 2.2.0 runtime and Tegra/input adapters. Requested streaming profiles go up to 1080p, not 4K. External Internet/VPN play needs separate network verification.

The public site reads website/published-release.json. Increasing source version does not publish new download URLs. The signed updater feed remains unchanged until the exact candidate assets are accepted and released.

[Setup](LINUX.md) · [Evidence boundaries](TESTED.md) · [Updates](UPDATES.md)
