# Build Deckivo

## Tested local toolchain

JDK 17.0.18; Android SDK platform 36, build-tools 36.0.0; NDK 30.0.16248370; CMake 4.4.4; Ninja; Python 3.14 with protobuf 7.34.2; protoc 34.1. Gradle wrapper 8.14.6, AGP 8.13.2, Kotlin 1.9.22. Android targetSdk 35, arm64-v8a only.

These versions describe the build that produced 0.1.2 and the Deckivo 0.2.0 toolchain, not a claim that every host/toolchain combination has been validated.

```sh
git clone https://github.com/remteh-by/remteh-remote-play.git
cd remteh-remote-play
git submodule update --init third-party/nanopb third-party/jerasure third-party/gf-complete third-party/curl android/app/src/main/cpp/oboe
python3 -m venv .buildenv
.buildenv/bin/python -m pip install protobuf==7.34.2
```

Set `JAVA_HOME` to JDK 17 and `ANDROID_HOME` to your Android SDK. Install the listed SDK/NDK/CMake components. `android/local.properties` is a local file for `sdk.dir` and, where necessary, `cmake.dir` (for example `/opt/homebrew` with Homebrew CMake); never commit it. CMake requires `protoc` in PATH. The first build downloads pinned Maven and CMake dependencies.

```sh
./android/gradlew -p android :app:assembleRelease :app:lintRelease :app:testReleaseUnitTest
```

The APK includes `android/app/src/main/assets/remteh-pair-helper.elf`, whose complete source is in `ps5-companion/`. To rebuild that separate ELF, install the open-source PS5 payload SDK and run:

```sh
PS5_PAYLOAD_SDK=/path/to/ps5-payload-sdk make -C ps5-companion
cp ps5-companion/remteh-pair-helper.elf android/app/src/main/assets/
```

Build and inspect the Android artifact again after changing any embedded ELF. On macOS the SDK may need `LLVM_CONFIG` pointing to the matching LLVM installation.

## Signing

`python3 scripts/sign-release.py` aligns and signs the release APK. It keeps the private key outside the source tree. The first use creates a local identity; maintainers of this distribution must retain the existing identity so updates can be installed over previous releases. Independent forks need their own identity/package name. Never upload a private key, password file or Android registration data.

The artifact filename is derived from `versionName`; every changed installable APK requires a new increasing `versionCode`. Publishing the already signed APK with unchanged bytes does not require another version increment.

## Source archive

The complete release source archive includes submodule files and native dependency sources under `vendor/`. When building from it, skip `git submodule update`; sources are already present. The current build files still resolve their pinned upstream dependencies, so an entirely offline build is not claimed.

## Optional host tests

```sh
clang -std=c11 -DHOST_TEST ps5-companion/main.c -o ps5-companion/companion-host
python3 tests/test_companion.py
python3 tests/test_decoder_lifecycle.py
```

These protocol/lifecycle tests do not replace physical Android decoding, controller, audio, reconnect or gameplay tests.

## Native desktop preview

Apple Silicon/macOS: `python3 desktop/macos/build-install.py --build N --stage-only`
uses the pinned packages in `desktop/macos/requirements.txt`, Homebrew SDL2 and
PyInstaller. The release bundle is ad-hoc signed, not Developer ID notarized.
The separately installed official chiaki-ng app is the native streaming engine.
Linux initial runtime and pairing: [docs/LINUX.md](docs/LINUX.md).

Native tests: run `QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s
desktop/linux/tests -v` with PyQt5 and cryptography installed. Android physical
acceptance and native unit tests are separate from gameplay evidence.

Public APKs must be built with `DECKIVO_UPDATE_FEED` unset. Private preview URLs,
keys, local registrations and device screenshots must never enter a public asset.
