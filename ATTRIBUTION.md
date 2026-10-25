# Attribution and licenses

Deckivo (formerly RemTeh Remote Play) is a modified distribution, not an independently reimplemented Remote Play protocol.

- **Immediate upstream:** [SalamiTheMan/chiaki-ng-android-extended](https://github.com/SalamiTheMan/chiaki-ng-android-extended), commit `478a20eab9e55651ae77035764cf3138bd14084b`. Its original README is retained in `docs/UPSTREAM-README.md` and its Git history is retained in this fork.
- **Chiaki and chiaki-ng:** the existing authors, contributors, file notices, history and license are retained. RemTeh does not claim authorship of their transport, cryptography, decoder stack or existing UI.
- **RemTeh changes (2026):** Android package/branding, local pairing/setup flow, input setup, PS/touchpad quick controls, build adaptations, the documented decoder lifecycle change, the verified GitHub updater and the RemTeh credit/support links. These client changes use the existing `LicenseRef-AGPL-3.0-only-OpenSSL` terms in `COPYING`.
- **PS5 companion:** separate executable `ps5-companion/main.c`, GPL-3.0-or-later. Registry key/formula provenance: [ps5-payload-dev/linkdev](https://github.com/ps5-payload-dev/linkdev), John Tornblom (2024), commit `8b1d47ed3acb5ead61602708ac1e58ad43f066f6`. Preserve its header and `ps5-companion/COPYING`.
- **PS5 toolchain:** [ps5-payload-dev/sdk](https://github.com/ps5-payload-dev/sdk); use its upstream license and build instructions when rebuilding the companion.
- **Dependencies:** Oboe, nanopb, curl, Jerasure, gf-complete, Mbed TLS, json-c, MiniUPnPc and other retained components remain under their own license files. Exact checked-out revisions for this build are listed in `UPSTREAM-LOCK.json`.

The source asset published with each APK includes initialized submodules and the native FetchContent source trees used for the build. The small GitHub-generated source archive alone does not expand Git submodules; use the attached complete source archive or clone with submodules.

The upstream support link in `.github/FUNDING.yml` is retained for the upstream author; it is not a RemTeh donation destination.

## Native frontend and media

- Deckivo's Python/Qt frontend is in `desktop/linux/`; platform entry points and
  helpers retain the project license. macOS uses separately installed official
  chiaki-ng; it is not bundled or claimed as RemTeh's protocol implementation.
- Linux runtime uses Ubuntu Chiaki 2.2.0. Its original source URL/hash are in
  `desktop/linux/UPSTREAM.json`; installation validates them.
- PyQt5, Qt, CPython, PyInstaller, truststore and SDL2 retain their upstream
  licenses. Exact Mac Python pins are in `desktop/macos/requirements.txt`.
  Bundled notices and upstream source locations are in `LICENSES/`.
- IBM Plex Sans: SIL Open Font License, included with the font.
- Original PS5/DualSense product photo: Sony Interactive Entertainment /
  PlayStation. Source, dimensions and SHA-256 are recorded in
  `design-system/assets/source.json`; no ownership or unrestricted-photo-license
  claim is made. It is displayed proportionally without invented geometry.

RemTeh's voluntary project support is [Ko-fi · RemTeh](https://ko-fi.com/pavelzayats).
The retained upstream Buy Me a Coffee link is a separate destination. Neither
link promises individual technical support from RemTeh.
