#!/bin/sh
set -eu
cd /work/build
mkdir -p qemu-out
cd qemu-out
../qemu-10.1.0/configure --target-list=aarch64-softmmu --without-default-features --without-default-devices --disable-debug-info --disable-docs --disable-tools --enable-fdt=system
ninja -j"${JOBS:-2}" qemu-system-aarch64
