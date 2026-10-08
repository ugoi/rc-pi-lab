# Image and application portability boundaries

- **Application:** `guest/app.py` calls original ServoKit and is installed with
  identical SHA256 in the guest. It contains no simulator imports, environment
  detection or monkeypatches. Actual execution on Stefan's physical Pi is pending.
- **Libraries:** exact original PyPI wheel hashes are locked. Guest wheel RECORD
  integrity is checked before demonstration. OS GPIO libraries come from the
  selected official Raspberry Pi OS image and are not replaced by lab shims.
- **Root filesystem:** official Raspberry Pi OS Bookworm Lite ARM64 is the base.
  Added files are under `/opt/rc-lab`, the lab systemd unit and its enable symlink,
  and a diagnostic `/rc-init`. Runtime state such as the journal changes on boot.
  This is a derived image, not an unchanged publisher image.
- **SD layout:** original boot partition, firmware, kernel and base DTBs are kept;
  application provisioning and I2C configuration are additions. The complete
  artifact uses the original partition offsets and a 4 GiB sparse container.
- **Virtual boot:** QEMU receives `kernel8.img` and a modified DTB externally.
  DT changes enable I2C1, disable the PL011 Bluetooth child and put PL011 on serial0,
  and supply `/system/linux,revision=0xa02082`, matching QEMU raspi3b.
  This bypasses real Raspberry Pi ROM/firmware loading and its DT overlay handling.
  QEMU UART, WiFi/SDIO, firmware GPIO and camera warnings are preserved in the log.
- **Real boot:** original firmware and physical kernel/DTB files remain available,
  but successful unchanged SD boot, real GPIO/I2C, the actual Pi variant, servo
  calibration and electrical operation have not been tested. No physical release
  is implied. The existing network Pi4 was not accessed.

The lab service runs only with the explicit kernel flag `rc_lab.demo=1`.
`rc_lab.poweroff=1` powers the guest off after a successful demonstration, for
repeatable image validation. A normal physical boot does not automatically move
an attached servo. Running this app on hardware requires an independently verified
servo pulse range and power arrangement.
