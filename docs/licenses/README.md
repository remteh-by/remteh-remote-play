# License inventory for 0.6.1

The APK has an offline “Licenses and source” screen from About/Updates and Support.
`assets/licenses/index.json` lists the shipped texts, including AGPL with the
upstream OpenSSL permission, the optional PS5 helper GPL, curl, Jerasure,
gf-complete, nanopb, Oboe, Mbed TLS, json-c, MiniUPnPc, AndroidX/Material/Kotlin/
Rx/Moshi Apache notices, ZXing Apache LICENSE/NOTICE, Reactive Streams CC0 and
IBM Plex Sans OFL. The source action goes to the exact v0.6.1 release.

Android's CMake sets `CHIAKI_LIB_ENABLE_OPUS=OFF`; an Opus library is not linked
into this APK, so this inventory does not claim that a separate bundled Opus
license is required. Keep this decision tied to the actual build flags. If the
flag changes, ship the corresponding license and source too.

Generate `:app:deckivoSbom` from the resolved Gradle runtime graph. It includes
artifact SHA-256 and exact native revisions from `UPSTREAM-LOCK.json`.
Generate the desktop CycloneDX using the same Python interpreter as the Mac
bundle. PyQt5 is GPL-3.0, Qt LGPL-3.0, PyQt5-sip BSD-2-Clause and truststore MIT;
the project retains all corresponding bundled license files in `LICENSES/`.
The desktop BOM describes this build's bundled Python runtime. System Ubuntu
libraries and the separately installed Mac chiaki-ng engine are external
prerequisites, not silently claimed as bundled/tested packages.

Primary Reactive Streams notice: https://github.com/reactive-streams/reactive-streams-jvm/blob/v1.0.3/COPYING
