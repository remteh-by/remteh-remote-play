#!/usr/bin/env bash
set -euo pipefail
# Invoke from the prepared chiaki-ng checkout in the MSYS2 UCRT64 shell.
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
  -DCHIAKI_ENABLE_CLI=OFF -DCHIAKI_ENABLE_TESTS=OFF \
  -DCHIAKI_ENABLE_STEAMDECK_NATIVE=OFF -DCHIAKI_ENABLE_STEAM_SHORTCUT=OFF -DCHIAKI_USE_SYSTEM_CURL=ON
cmake --build build --target chiaki --parallel "${DECKIVO_JOBS:-4}"
