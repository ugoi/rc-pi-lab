#!/bin/sh
set -eu
cd /work/build
printf '%s\n' '62d025b9bc7ca0e1facfec74ae56ac13978b6745c58177f081d39fbb8041ed45  base.img.xz' | sha256sum -c -
sha256sum base.img.xz qemu-10.1.0.tar.xz > /work/evidence/input-sha256.txt
test -f base.img || xz -dc base.img.xz > base.img
mkdir -p boot
mcopy -o -i base.img@@8388608 ::kernel8.img ::bcm2710-rpi-3-b.dtb boot/
dd if=base.img of=rootfs.img bs=1M skip=520 count=2112 status=none
for f in /usr/bin/python3 /usr/bin/pip3 /usr/lib/python3/dist-packages/RPi /lib/modules; do debugfs -R "ls $f" rootfs.img; done
