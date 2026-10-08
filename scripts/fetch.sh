#!/bin/sh
set -eu
mkdir -p build evidence
cd build
fetch() { test -f "$2" || curl --fail --location --retry 2 "$1" -o "$2"; }
fetch https://download.qemu.org/qemu-10.1.0.tar.xz qemu-10.1.0.tar.xz
fetch https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-2025-05-13/2025-05-13-raspios-bookworm-arm64-lite.img.xz base.img.xz
printf '%s\n' \
'e0517349b50ca73ebec2fa85b06050d5c463ca65c738833bd8fc1f15f180be51  qemu-10.1.0.tar.xz' \
'62d025b9bc7ca0e1facfec74ae56ac13978b6745c58177f081d39fbb8041ed45  base.img.xz' | sha256sum -c -
