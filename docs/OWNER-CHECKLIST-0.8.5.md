# Deckivo 0.8.5 — device acceptance

Android is 0.8.5 / versionCode 30; macOS and Switchroot Ubuntu are 0.8.5 / build 21.
Update over the existing app and keep its registration. Do not downgrade or erase
app data to manufacture an update test. Keep controller Service mode off for
ordinary checks; no permanent calibration or firmware write is part of this release.

- **Switch Android:** use the normal public updater from the actual installed build;
  compare the installed APK SHA with the release. Verify pairing, saved consoles,
  language selection, settings and restart. Test picture, sound, controls and a
  30-minute session, then Wi-Fi reconnect and sleep/wake. Measure frame loss,
  decoder/hardware selection, thermal state and latency before claiming lag fixed.
- **Switch Ubuntu:** use its signed public updater to b21, with the GUI open and
  via the enabled user timer. Verify receipt/acknowledgment, retained registration,
  login timer, Wi-Fi password persistence after reboot, sound, controller capture
  and a 30-minute session. No physical b21 acceptance has yet been recorded.
- **PS5 online:** verify local connection, reconnect and saved-game launch. Offline
  status and updater acceptance alone do not certify streaming or internet/VPN play.
- **Controllers:** test each available DualSense, DualShock 4, Xbox or other pad,
  USB and Bluetooth separately. Verify sticks, triggers, buttons, vibration,
  PS/Touch and unsupported-feature messages. Mock tests do not prove physical
  calibration behavior. Follow the EN/RU guide before any separately authorized
  service operation; a corrupt backup must block permanent writes.
- **Mac gameplay:** verify WASD, mouse aiming, all five mouse buttons, custom
  bindings, sensitivity, keyboard layout and focus loss/return in a real game.
- **First Mac launch:** test the downloaded archive with a fresh macOS user and
  Gatekeeper enabled. The app is ad-hoc signed, not notarized. Updating an already
  accepted installation does not test first-run Gatekeeper behavior.
- **Donations:** Ko-fi navigation is separate from an actual payment receipt.
  No payment is submitted during these checks.
