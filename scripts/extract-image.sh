#!/bin/sh
set -eu
cd /work/build
test ! -e rootfs.img || { echo "Refusing to overwrite existing rootfs.img" >&2; exit 1; }
printf '%s\n' '62d025b9bc7ca0e1facfec74ae56ac13978b6745c58177f081d39fbb8041ed45  base.img.xz' | sha256sum -c -
sha256sum base.img.xz qemu-10.1.0.tar.xz > /work/evidence/input-sha256.txt
if test ! -f base.img; then
    # XZ 5.8 defaults to host-wide automatic threads, not the cgroup budget.
    # Explicit options override XZ_DEFAULTS; leave headroom in the 2-GiB container.
    trap 'rm -f base.img.tmp' EXIT HUP INT TERM
    xz --threads=1 --memlimit-decompress=256MiB -dc base.img.xz > base.img.tmp
    mv base.img.tmp base.img
    trap - EXIT HUP INT TERM
fi
mkdir -p boot
mcopy -o -i base.img@@8388608 ::kernel8.img ::bcm2710-rpi-3-b.dtb boot/
dd if=base.img of=rootfs.img bs=1M skip=520 count=2112 status=none
# QEMU SD storage requires a power-of-two container; ext4 geometry is unchanged.
truncate -s 4G rootfs.img
for f in /usr/bin/python3 /usr/bin/pip3 /usr/lib/python3/dist-packages/RPi /lib/modules; do debugfs -R "ls $f" rootfs.img; done
