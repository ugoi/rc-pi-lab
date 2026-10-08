#!/bin/sh
set -eu
cd /work
exec build/qemu-out/qemu-system-aarch64 \
  -M raspi3b -m 1G -smp 4 -nographic -monitor none \
  -kernel build/boot/kernel8.img -dtb build/boot/qemu-rpi3.dtb \
  -drive file=build/rc-pi3.img,format=raw,if=sd \
  -append 'console=ttyAMA0,115200 root=/dev/mmcblk0p2 rootwait rw earlycon=pl011,mmio32,0x3f201000 rc_lab.demo=1 rc_lab.poweroff=1 systemd.unit=multi-user.target panic=-1' \
  -chardev socket,id=pwm,path=/work/build/pwm.sock,server=on,wait=off \
  -device pca9685,bus=i2c-bus.1,address=0x40,chardev=pwm,trace-file=/work/evidence/pca-image.jsonl
