# Attribution and licenses

RemTeh Remote Play is a modified distribution, not an independently reimplemented Remote Play protocol.

- **Immediate upstream:** [SalamiTheMan/chiaki-ng-android-extended](https://github.com/SalamiTheMan/chiaki-ng-android-extended), commit `478a20eab9e55651ae77035764cf3138bd14084b`. Its original README is retained in `docs/UPSTREAM-README.md` and its Git history is retained in this fork.
- **Chiaki and chiaki-ng:** the existing authors, contributors, file notices, history and license are retained. RemTeh does not claim authorship of their transport, cryptography, decoder stack or existing UI.
- **RemTeh changes (2026):** Android package/branding, local pairing/setup flow, input setup, PS/touchpad quick controls, build adaptations and the documented decoder lifecycle change. These client changes use the existing `LicenseRef-AGPL-3.0-only-OpenSSL` terms in `COPYING`.
- **PS5 companion:** separate executable `ps5-companion/main.c`, GPL-3.0-or-later. Registry key/formula provenance: [ps5-payload-dev/linkdev](https://github.com/ps5-payload-dev/linkdev), John Tornblom (2024), commit `8b1d47ed3acb5ead61602708ac1e58ad43f066f6`. Preserve its header and `ps5-companion/COPYING`.
- **PS5 toolchain:** [ps5-payload-dev/sdk](https://github.com/ps5-payload-dev/sdk); use its upstream license and build instructions when rebuilding the companion.
- **Dependencies:** Oboe, nanopb, curl, Jerasure, gf-complete, Mbed TLS, json-c, MiniUPnPc and other retained components remain under their own license files. Exact checked-out revisions for this build are listed in `UPSTREAM-LOCK.json`.

The source asset published with each APK includes initialized submodules and the native FetchContent source trees used for the build. The small GitHub-generated source archive alone does not expand Git submodules; use the attached complete source archive or clone with submodules.

The upstream support link in `.github/funding.yml` is retained for the upstream author; it is not a RemTeh donation destination.
