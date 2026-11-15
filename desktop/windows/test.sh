#!/usr/bin/env bash
set -eu
engine=$(cd "$1" && pwd)
repo=$(cd "$(dirname "$0")/../.." && pwd)
cd "$repo"
moc=$(find "$engine/build/gui/chiaki_autogen" -name moc_windows_tools.cpp -print -quit)
test -f "$moc"
out="$engine/build/deckivo-windows-tests.exe"
g++ -DSDL_MAIN_HANDLED -Wno-sfinae-incomplete -std=c++17 -O0 desktop/windows/test-input-history.cpp \
    "$moc" "$(dirname "$moc")/moc_windows_update.cpp" \
    -I"$engine/gui/include" -I"$engine/lib/include" -I"$engine/build/lib/include" \
    $(pkg-config --cflags --libs Qt6Widgets Qt6Network sdl2 openssl) \
    "$engine/build/lib/libchiaki.a" -lcrypt32 -o "$out"
QT_QPA_PLATFORM=offscreen "$out"
