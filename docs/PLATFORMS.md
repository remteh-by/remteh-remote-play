# Platform scope

| Target | 0.6.0 delivery | Evidence |
|---|---|---|
| Android ARM64 | Native APK; Android 8+ declared minimum | Physical Switch OLED / Android 15; see exact version matrix |
| macOS Apple Silicon | Frozen native Qt app; separate official chiaki-ng engine; ad-hoc signature, no notarization | macOS 27.0.1; earlier engine stream and 0.5.1 updater tests |
| Switchroot Ubuntu ARM64 | Native Python/Qt developer source and upgrade pack | Switch OLED, Ubuntu 24.04.4 / KDE X11 / FFmpeg 6.1; earlier stream and 0.5.1 updater tests |
| Windows x64 | Planned | No Deckivo build or device acceptance |
| macOS Intel | Planned | No Deckivo build or device acceptance |
| Desktop Ubuntu/Linux x64 | Planned | No Deckivo build or device acceptance |
| Other OSes | Research | No delivery claim |

Brand, design assets and language catalogs are shared. Android uses the retained
C/Kotlin Remote Play core. Mac uses an installed chiaki-ng 1.10.0 engine through
native helpers; Linux isolates Ubuntu Chiaki 2.2.0 with a Tegra/input adapter.
An Android APK is not a Windows or desktop Linux application.

Local play does not require a permanent home PC or a new Deckivo account.
External Internet play is separate: routing/authentication/VPN and real external
network tests remain open. A travelling MacBook and an off home PC do not supply
an always-on home gateway.

See [TESTED.md](TESTED.md) and the [16 guides](guides/en.md).
