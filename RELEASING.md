# Publishing a version

Pre-1.0 versions are experimental prereleases. The owner’s standing instruction of 2026-10-25 is to publish ready Deckivo updates on GitHub and verify their delivery; a local build or install alone does not complete an update. Complete artifact checks, keep a truthful device/version test matrix, and include matching source and license notices. Do not present a prerelease as a stable 1.0 release. Preserve existing tags and release assets.

Repository: `remteh-by/remteh-remote-play`. Release tags use `vX.Y.Z`.

1. Update `android/app/build.gradle`: meaningful compatible feature → MINOR, fix/cosmetic change → PATCH, incompatible change → MAJOR. Increase Android `versionCode` for every changed APK. Update `CHANGELOG.md` and the release notes.
2. Build, run checks appropriate to the change and record what was actually tested. Keep untested long sessions, internet access and physical device combinations explicit.
3. Sign with the existing local key. Keep the private signing material outside Git and GitHub Actions.
4. Generate `update.json` with `JAVA_HOME=/path/to/jdk17 python3 scripts/update-manifest.py dist/Deckivo-X.Y.Z-arm64.apk --output dist/update.json`. This reads the actual APK package/version/size/SHA-256. Then prepare the complete corresponding source archive, retaining upstream notices, submodule sources, native dependencies, `COPYING` and `ps5-companion/COPYING`. Publish the APK, the separate helper ELF if included, this archive, validation report and SHA-256 sums together. Do not upload the private local diagnostics kit unchanged.
5. Check the public files for local profile names, account IDs, registration keys, credentials, device logs and personal filesystem paths. Verify the artifact version/code and signing certificate; compare APK bytes with the build that was tested. The 0.1.2 APK includes native library compile-time source path strings; it contains no registration or account database. Remove build-host paths from future native builds before their next version is produced.
6. Commit the reviewed source and documentation, create `vX.Y.Z` at that commit and push the branch/tag to this repository, not upstream. Do not move an already published tag or replace an APK under the same version.
7. Create a draft GitHub release with `--verify-tag` and attach all files. Read back their names, sizes, hashes and source tag. Publish the draft only after validation; keep experimental versions marked prerelease.

Example (replace the version and file paths):

```sh
git tag -a vX.Y.Z -m "Deckivo X.Y.Z"
git push origin main
git push origin vX.Y.Z
gh release create vX.Y.Z --repo remteh-by/remteh-remote-play --verify-tag --draft --prerelease --title "Deckivo X.Y.Z" --notes-file release-notes.md APK FILES SOURCE_ZIP SHA256SUMS.txt validation.json
```

After reviewing the actual draft assets, publish it with `gh release edit vX.Y.Z --repo remteh-by/remteh-remote-play --draft=false`. GitHub publication alone does not install the update on Android. Versions starting with 0.2.0 read the `update.json` asset from this repository. Generate it from the signed APK with `scripts/update-manifest.py`, publish it with the exact APK and source, and test both manual checks and installation. Never change the applicationId or signing key to rebrand the app. The repository slug stays stable for existing update feeds.

## Completion includes delivery

- Publish the tag, release notes, exact signed platform packages, corresponding
  source and licenses, hashes and verification report together. Keep prerelease
  status while the product is experimental.
- Publish Android `update.json` and the signed desktop `updates/index.json` /
  `index.sig` for the platforms actually released. The site and README must link
  to those exact artifacts; do not advertise a nonexistent build for another OS.
- Read back public versions, package sizes and SHA-256 values, verify signatures
  and confirm the update candidate from each supported client. Publication and
  actual on-device installation are separate checks.
- An update with a concrete failing build/test/release blocker remains incomplete:
  name the blocker and the last delivered version. Never silently leave the only
  new version on the developer’s computer or claim unperformed hardware tests.
- Download statistics refresh from GitHub release asset counters at site deploy,
  release publication/edit, and the hourly scheduled Pages build. They count
  repeated/automatic/verification downloads too; they are not unique users.

## Red flag: screenshots must match the app

An outdated GitHub or Pages screenshot is a release defect. Every UI-changing
release must capture the actual app, refresh the README cover, Pages AVIF/WebP
and relevant guide images, and verify the public rendered result. Keep real
console/controller photographs; never replace the application view with a mockup.
Use isolated empty profile storage to exclude account IDs, keys and personal data.
Record the exact screenshot version/build, source revision and image hashes.
A development preview shown before publication must be labelled explicitly;
its caption must not imply that the older downloadable release contains that UI.
