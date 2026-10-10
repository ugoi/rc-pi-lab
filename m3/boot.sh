#!/bin/sh
set -eu
cd /work
extra=""
if [ "${M3_REUSE_AUDIT:-0}" = 1 ]; then extra="$extra m3.reuse_audit=1"; fi
if [ "${M3_TESTING:-0}" = 1 ]; then extra="$extra m3.test_faults=1"; fi
exec build/qemu-out/qemu-system-aarch64 \
 -M raspi3b -m 1G -smp 4 -snapshot -display none -monitor none \
 -kernel build/boot/kernel8.img -dtb build/boot/qemu-rpi3.dtb \
 -drive file=build/m3/rootfs.img,format=raw,if=sd \
 -append "console=ttyAMA0,115200 root=/dev/mmcblk0 rootwait rw init=/m3-init panic=-1$extra" \
 -chardev socket,id=serial,path=/work/build/m3/serial.sock,server=on,wait=off \
 -serial chardev:serial \
 -chardev socket,id=pwm,path=/work/build/m3/pwm.sock,server=on,wait=off \
 -device pca9685,bus=i2c-bus.1,address=0x40,chardev=pwm,trace-file=/work/evidence/m3/pca.jsonl
