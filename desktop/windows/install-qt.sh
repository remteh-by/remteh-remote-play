#!/usr/bin/env bash
# Install the tested Qt host tools and matching runtime in Deckivo's UCRT64 build environment.
set -euo pipefail
[[ ${MSYSTEM:-} == UCRT64 ]] || { echo "Run in the project's MSYS2 UCRT64 shell" >&2; exit 1; }
cache=$(mktemp -d)
cd "$cache"
names=(
    mingw-w64-ucrt-x86_64-qt6-base-6.11.2-2-any.pkg.tar.zst
    mingw-w64-ucrt-x86_64-qt6-declarative-6.11.2-1-any.pkg.tar.zst
    mingw-w64-ucrt-x86_64-qt6-svg-6.11.2-1-any.pkg.tar.zst
)
hashes=(
    ccc98698391f78419de72640175508a68b7ba9e25a43a54e01a05b51079ad6a2
    e6f303088cf9c33c45404c3c7331fd40c785248ae5eba1fbd97d4b6daf506335
    964fee6a84ed92b474e345f1dfe8269b2f600eb62e5a7fc353be214a5b4c3996
)
gpg --dearmor < /usr/share/pacman/keyrings/msys2.gpg > keyring.gpg
for index in "${!names[@]}"; do
    file=${names[index]}
    for suffix in '' .sig; do
        curl -fsSLO "https://repo.msys2.org/mingw/ucrt64/$file$suffix"
    done
    printf '%s  %s\n' "${hashes[index]}" "$file" | sha256sum -c -
    gpgv --keyring ./keyring.gpg "$file.sig" "$file"
done
pacman -U --needed --noconfirm "${names[@]}"
