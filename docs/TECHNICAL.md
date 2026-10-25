# Technical reference and troubleshooting

## Account and registration

Use the Account ID belonging to the currently selected PS5 profile in Base64
form. A display name/email is not an Account ID. The eight-digit code from PS5
Settings → System → Remote Play → Link Device expires; request a fresh one.
Android's optional local ELF helper uses a different challenge code. It only
works when your own console already supports running that ELF. It is not needed
for standard Remote Play and does not activate accounts or modify saves.

Mac imports an existing local registration from the separately installed
[official chiaki-ng](https://github.com/streetpea/chiaki-ng/releases). Register
there first, close its stream, then use the import action in Deckivo Preferences.
Linux uses `python3 desktop/linux/pair.py` from the complete source kit.

## Network

First test both devices on the same trusted home network. Enter the PS5's actual
IPv4 address in your installation, not an address copied from someone else's
screenshot. A guest network, client isolation, stale DHCP address, blocked DNS or
an unavailable custom gateway can prevent communication. Deckivo does not change
router rules or guarantee Sony update blocking. No pairing keys belong in a
public website or public bug report. Do not expose helper/control ports directly
to the Internet. Internet/VPN play needs its own route and acceptance test.

## Black screen / no audio / no controls

Save the game when possible, end the stream, close any competing Remote Play
clients and reconnect. Try 720p, lower bitrate or 30 FPS. Confirm that the gamepad
is paired to the OS actually running on Switch; Bluetooth pairing in Android
is separate from Ubuntu. Check audio output and volume. An observed 720p frame
or requested 60 FPS is not evidence of sustained rendered 60 FPS.

If PS5 WebKit hangs, diagnose the console separately. Remote Play itself uses
Sony's built-in service; Deckivo does not repair a kernel exploit or make a
console-side game launch successfully. The app never asks to update PS5 firmware.

## Update recovery

Keep your app data. Install the exact release APK/app over the old client rather
than uninstalling. Android refuses a different signing key or lower versionCode.
Use the source-specific permission only if Android asks. Leave Play Protect and
TLS verification enabled. Mac's ad-hoc bundle can need an intentional per-app
Open Anyway approval; it is not notarized. Never disable Gatekeeper globally.
Desktop rollback and source migration are explained in [UPDATES.md](UPDATES.md).

## Useful evidence

Report platform, OS, Deckivo version/build, visible error and what action caused
it. Use the allowlisted desktop diagnostic export when available; never attach
registration files, keys, account IDs, PINs, payment data or raw private logs.
Donations do not imply individual setup service.
