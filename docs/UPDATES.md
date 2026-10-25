# Deckivo updates

## Public 0.6.0 channel

The public release is experimental. Keep preview releases enabled if you want
0.x updates. Install over the existing application; never clear registration data
as a normal update step. No private key, registration or account database is in
release packages.

| Client | Check/download | Installation |
|---|---|---|
| Android ARM64 | GitHub Releases, home/update screen open, normally every six hours; manual check immediately; automatic download on unmetered Wi-Fi | Same package and certificate verified; Android 12+ native self-update after source permission, with system confirmation whenever Android requires it |
| macOS Apple Silicon | RSA-signed index at the public Pages channel, automatic checks while Deckivo is open | Waits for idle dashboard, verifies bundle identity/build/codesign, replaces app and relaunches; startup acknowledgment or rollback |
| Switchroot Ubuntu ARM64 | Same signed public metadata and exact archive hash | Waits for idle state; compiles adapter against installed headers; transactionally replaces client files, retains runtime/registration/settings/history |

Public native metadata:
`https://remteh-by.github.io/remteh-remote-play/updates/`.
Packages are exact assets of `remteh-by/remteh-remote-play` releases over HTTPS.
The RSA public key is pinned in the client. Android independently verifies the
existing APK certificate in addition to release metadata and file hashes.

### Once, when migrating older private builds

- Android private builds 18–20 use the earlier LAN feed. Install the public APK
  over them once, or receive the same public APK through the old private feed.
  Future checks then use GitHub. The package remains `by.remteh.remoteplay`.
- Older Mac builds need the 0.6.0 public app once (or a private bootstrap carrying
  this code). The new client ignores an old cleartext channel configuration
  unless it explicitly opts into private preview mode.
- Existing Ubuntu installs can run the 0.6.0 upgrade pack once. A fresh device
  needs the initial runtime first; see [Linux requirements](LINUX.md).

### What automatic does and does not mean

The app must be open and the network available. A sleeping device/closed app is
not a permanent background service. Active gameplay defers installation.
Downloads may be cancelled when changing screens; incomplete files are discarded.
Android may still ask for installation or Play Protect confirmation; the app does
not bypass those controls. Mac builds are not notarized. No operating-system,
console-firmware or chiaki-ng engine update is silently installed by this updater.

### Verification and rollback

Reject wrong platform/package, non-increasing builds, lower versions, untrusted
URLs, oversized files, bad hashes/signatures and invalid archive paths. Mac bundle
updates retain an old app and need a matching startup acknowledgment; a failed
archive is quarantined. Linux keeps a versioned rollback directory and restores
files on a failed replacement. Never publish a different APK under the same
Android versionCode or move an existing release tag.

The physical 0.5.1 transitions are in [TESTED.md](TESTED.md). Public release
availability alone is not evidence of successful device installation.

## Maintainer

Generate `update.json` from the actual signed APK with
`scripts/update-manifest.py`. Generate the signed desktop index with
`scripts/package-public-release.py`; keep RSA/APK private keys outside Git and
CI. Publish exact packages, complete corresponding source, validation and
SHA256SUMS together. Never publish private channel URLs or device logs.
