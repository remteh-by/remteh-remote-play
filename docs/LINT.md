# Android Lint reconciliation — 0.6.1

The old 0.6.0 report had 249 warnings: 85 in new Deckivo files, 68 in files
modified by Deckivo, 96 only in unchanged upstream files. “All existing” was
incorrect. The v0.6.0 tag and published files remain unchanged.

`android/lint-baseline.xml` contains only the 96 unchanged upstream findings,
classified against `159a9b4^` (the immediate pre-Deckivo source). The directory
finding for `mipmap-anydpi-v26` refers to unchanged upstream icon files.
No new/modified Deckivo file's warning is put in this baseline.

Corrections include AndroidX edit/toUri, resource-based text, consistent Kotlin
indentation, scalable vector intrinsic dimensions, API-qualified font variation,
ConstraintLayout columns instead of nested weighted ancestors, complete layout
IDs, decorative image semantics, unused resource/menu removal, FragmentContainerView,
and explicit backup exclusions for cloud and device transfer.

Three intentional, narrowly scoped diagnostics are documented rather than
“fixed” by breaking functionality:
- `HighSamplingRate` on the one sensor permission: existing StreamInput requests
  4000 µs / 250 Hz motion data; removing permission changes Remote Play motion.
- `AppBundleLocaleChanges` on LanguagePicker: this universal sideload APK contains
  all locales, with language splits disabled. There are no Play Core language modules.
- `UnsafeNativeCodeLocation` only for `remteh-pair-helper.elf`: this is a PS5 ELF
  uploaded over LAN, never an Android process/library.

Compiler/kapt/Gradle deprecation notices are a separate class from Android Lint;
this release does not pretend to eliminate upstream toolchain warnings.
