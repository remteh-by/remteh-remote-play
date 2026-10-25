# Publishing a version

Pre-1.0 versions are experimental prereleases. Publication requires an explicit owner instruction, completed artifact checks, a truthful device/version test matrix, matching source and license notices. Do not present a prerelease as a stable 1.0 release. Preserve existing tags and release assets.

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
