#!/bin/sh
set -eu
modprobe i2c-bcm2835
modprobe i2c-dev
echo '=== STE91 SYSTEMD GUEST ==='
uname -a
cat /etc/os-release
dpkg-query -W python3 python3-rpi-lgpio python3-lgpio
cat /proc/cpuinfo
tr '\000' '\n' < /proc/device-tree/model
ls -l /dev/i2c*
python3 -u /opt/rc-lab/verify_packages.py
python3 -u /opt/rc-lab/probe.py
python3 -u /opt/rc-lab/app.py
echo SYSTEMD_DEMO_PASS
case " $(cat /proc/cmdline) " in
  *" rc_lab.poweroff=1 "*) sync; systemctl --no-block poweroff ;;
esac
