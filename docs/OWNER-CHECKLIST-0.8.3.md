# Deckivo 0.8.3 — physical acceptance still required

The device was unavailable during this release. Keep registrations and app data;
install updates over the current app. Never uninstall first. Do not permanently
calibrate or flash controllers as part of this checklist.

1. Android: run the normal updater from #25 to the retained 0.8.2 #27, then to
   0.8.3 #28. Compare the installed base APK SHA-256 with each release. Confirm
   the saved PS5 card, pairing, Auto/RU/EN after restart and streaming, support
   QR, licenses and localized update dialogs.
2. Record the current Android stream settings. On the same scene, measure each
   profile for three minutes, changing one property at a time: H.264 720p60 at
   about 8 Mbps with debanding off; 540p30 at 5 Mbps; then restore 1080p, H.265,
   debanding and high bitrate separately. Reset to the baseline before each
   separate restoration. Record actual effective values, not only requested ones.
3. For every run collect MediaCodec name/hardware status; received, decoded,
   presented and dropped frames; decoder latency; packet loss and FEC; Wi-Fi
   RSSI/frequency; temperature/throttling and CPU/GPU frequency/load. Useful
   Android sources include logcat, `dumpsys thermalservice`, `dumpsys wifi`,
   `dumpsys media.codec`, `dumpsys gfxinfo by.remteh.remoteplay` and `top`.
   These commands may not expose every metric: explicitly mark unavailable data.
   Repeat the same scenario after any evidence-based fix before choosing a default.
4. Ubuntu: use normal signed updates b17 → retained 0.8.2 b18 → 0.8.3 b19.
   Check launch, pairing, Donate without crash, streaming and a full reboot.
   Verify `systemctl --user cat deckivo-update-login.timer deckivo-update.timer`:
   45-second initial check; 60-minute repeat with 10-minute random delay. Verify
   the Git noreply identity in the Ubuntu source checkout when reachable.
5. Play at least 30 minutes on Android and 30 on Ubuntu. Check picture, sound,
   sticks, D-pad, face/shoulder buttons, analog L2/R2, PS and Touch, pause/return,
   Wi-Fi reconnect, sleep/wake and clean stream shutdown. Collect the same metrics.
6. Mac: in a real game verify WASD, aim, five mouse buttons, saved bindings,
   EN/RU keyboard layout, focus loss/return and quick play after the b19 update.
   Update acceptance by itself does not certify gameplay or input.
7. For each physically available DualSense, DualShock 4 and Xbox controller,
   test USB and Bluetooth independently: buttons, analog triggers, vibration,
   light and touchpad where supported. Mark unsupported features and absent
   hardware explicitly. Keep Service mode off for routine input tests.

Owner-only decisions: Ko-fi Settings → Payments; USDT TRC20 / TON addresses if
desired; prepared Ko-fi copy in `docs/marketing`; whether to keep or remove Sony
firmware files from remteh.by. No payment or production website change is part
of the Deckivo release.
