# Deckivo updates

## Public channel: Linux 0.8.1, Android and macOS 0.6.1

The public release is experimental. Keep preview releases enabled if you want
0.x updates. Install over the existing application; never clear registration data
as a normal update step. No private key, registration or account database is in
release packages.

| Client | Check/download | Installation |
|---|---|---|
| Android ARM64 | GitHub Releases, home/update screen open, normally every six hours; manual check immediately; automatic download on unmetered Wi-Fi | Same package and certificate verified; Android 12+ native self-update after source permission, with system confirmation whenever Android requires it |
| macOS Apple Silicon | RSA-signed index at the public Pages channel, automatic checks while Deckivo is open | Waits for idle dashboard, verifies bundle identity/build/codesign, replaces app and relaunches; startup acknowledgment or rollback |
| Switchroot Ubuntu ARM64 | Signed public metadata and exact archive hash; since 0.8.1 a user timer also stages updates while the app is closed | Applies on the idle dashboard, including at the next launch; compiles adapters against installed headers; retains runtime/registration/settings/history; matching startup acknowledgment within 120 seconds or file rollback |

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

On Android and macOS the app must be open and the network available. Ubuntu
0.8.1 also checks with a systemd user timer while the user is logged in and the
device is awake: about 45 seconds after login, then about every two minutes.
It stages a signed package without opening a window. Installation waits for the
next idle Deckivo dashboard; an active stream always defers installation.
A sleeping or powered-off device cannot check. Failed network checks retry on
the next timer run, and a previously verified staged package remains available
offline. Turning automatic updates off disables this timer too.
Downloads may be cancelled when changing screens; incomplete files are discarded.
Android may still ask for installation or Play Protect confirmation; the app does
not bypass those controls. Mac builds are not notarized. No operating-system,
console-firmware or chiaki-ng engine update is silently installed by this updater.

### Verification and rollback

Reject wrong platform/package, non-increasing builds, lower versions, untrusted
URLs, oversized files, bad hashes/signatures and invalid archive paths. Mac bundle updates retain an old app. In 0.6.1 both Mac and Linux require a
matching transaction and new-process PID acknowledgment within 120 seconds.
The acknowledgment comes from the shown main window's event loop after loading
settings/registration and checking that the engine exists, not after a stream.
A failed live child is terminated before restoring a bundle/files. If it cannot
be stopped, restoration is refused to avoid mutating a running installation.
Linux restores from the exact backup receipt, including removal of new files;
pairing and runtime paths are outside the upgrade allowlist.
Linux 0.8.1 includes the previously missing `upgrade.py` in installed files,
fixing the first update from a clean 0.6.1 installation. GUI and background
downloads share a lock; signed metadata and packages use immutable hash-based
cache paths, so another check cannot change an in-progress transaction.
0.6.0 Linux only rolled back a failed replacement, not a missing startup ack;
0.6.0 Mac used 30 seconds. Those historical limitations were corrected in 0.6.1.
RSA verification now uses strict pure Python SPKI/PKCS#1 v1.5 SHA-256, without
calling external openssl. Signing tools used by maintainers are separate. Never publish a different APK under the same
Android versionCode or move an existing release tag.

The physical 0.5.1 transitions are in [TESTED.md](TESTED.md). Public release
availability alone is not evidence of successful device installation.

## Maintainer

Generate `update.json` from the actual signed APK with
`scripts/update-manifest.py`. Generate the signed desktop index with
`scripts/package-public-release.py`; keep RSA/APK private keys outside Git and
CI. Publish exact packages, complete corresponding source, validation and
SHA256SUMS together. Never publish private channel URLs or device logs.

The future custom domain is not active. See [domain migration](marketing/domain.md) before adding any CNAME.
