#!/bin/sh
set -eu
cp build/boot/bcm2710-rpi-3-b.dtb build/boot/qemu-rpi3.dtb
fdtput -t s build/boot/qemu-rpi3.dtb /soc/i2c@7e804000 status okay
fdtput -t s build/boot/qemu-rpi3.dtb /soc/serial@7e201000 status okay
fdtput -t s build/boot/qemu-rpi3.dtb /soc/serial@7e201000/bluetooth status disabled
fdtput -t s build/boot/qemu-rpi3.dtb /aliases serial0 /soc/serial@7e201000
fdtput -t s build/boot/qemu-rpi3.dtb /aliases serial1 /soc/serial@7e215040
# Firmware normally supplies this; it matches QEMU raspi3b's board_rev.
fdtput -cp build/boot/qemu-rpi3.dtb /system
fdtput -t x build/boot/qemu-rpi3.dtb /system linux,revision a02082
fdtget build/boot/qemu-rpi3.dtb /soc/i2c@7e804000 status
sha256sum build/boot/kernel8.img build/boot/bcm2710-rpi-3-b.dtb build/boot/qemu-rpi3.dtb > evidence/boot-input-sha256.txt
