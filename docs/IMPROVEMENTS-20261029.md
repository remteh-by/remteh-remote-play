# Audit candidate — 29 October 2026

This branch is a candidate based on 0.8.6 (Android 31, desktop build 22), not a new public release. Existing signing identities, user registrations and public update metadata are retained. A release needs a separate version/build assignment and device acceptance.

## Changes

- Android update scheduling distinguishes successful checks, lifecycle cancellation, transient errors and server rate limits. Cancellation uses short request spacing rather than the six-hour success interval. Manual requests respect server deadlines; transient failures use bounded backoff.
- Desktop Controller Lab reports page presence over its loopback server. Closing its window or a failed browser launch releases the launcher controller monitor. Chrome profile handoff and background-window timer throttling are accounted for. Calibration storage and the bundled tester remain intact.
- The desktop shell, input editor and update UI use a generated catalog for 16 languages. Auto resolves the system locale consistently; Arabic uses RTL. Controller Lab itself still supports EN/RU and says so before opening.
- Ubuntu X11 gains persisted physical-key assignments, five mouse buttons, sensitivity and inversion. Escape/F8 and focus loss release input. This Qt5 overlay explicitly declines mouse capture under Wayland rather than claiming unsupported pointer capture.
- macOS detects the expected official chiaki-ng bundle in system/user Applications and supports selecting another location. Bundle metadata, executable permissions and ARM64 architecture are checked; invalid explicit choices do not silently fall back. Engine selection survives preference validation.
- Engine detection reads bounded Mach-O headers directly. Frozen packages verify the SDL library ID at build time, avoiding a runtime dependency on Xcode developer tools when preparing the private engine copy.
- FAQ versions and package names follow the application version/build. Checks cover rendered FAQ/schema/download consistency. Android native builds now quote source-prefix mappings for paths containing spaces.
- Android saves an allow-listed local stream diagnostic snapshot and offers export from session history. Decoded buffers, Surface submissions and receiver loss are separate counters. Decoder name/acceleration, actual dimensions, presented/dropped display frames and queue latency stay unknown until measured; Surface submission does not certify display presentation.

## Checks

The candidate has regression coverage for update cancellation/backoff, locale resolution, Controller Lab lifecycle, physical key mapping, side mouse buttons, engine selection and FAQ versions. Packaging checks verify that new runtime modules and translations are included in Linux updates and the frozen Mac app. Tests, lint, native compilation and offscreen layout checks are distinct from physical-device acceptance.

## Still requires real devices

- PS5 streaming, audio/input and a sustained session on Mac, Switch Android and Switch Ubuntu.
- Android performance comparison at 720p/60 and 1080p/60, reconnect/sleep, and real update installation preserving registration.
- USB/Bluetooth controller tests across DualSense, DualShock 4, Xbox and other compatible controllers; first-user Mac Gatekeeper check.
- Native review of translation drafts, real donation navigation/payment where authorized, and live-window visual acceptance. Offscreen captures cannot certify the installed window.

No verified 4K streaming mode, general Windows build, or universal Ubuntu support is claimed. Existing Linux source updates target the retained Switchroot ARM64 runtime.
