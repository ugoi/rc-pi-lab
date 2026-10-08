# Source ledger — 2026-10-08

- QEMU 10.1.0, GPL-2.0 (individual files may have compatible licenses):
  https://download.qemu.org/qemu-10.1.0.tar.xz
  Release commit `f8b2f64e2336a28bf0d50b6ef8a7d8c013e9bcf3`.
  https://github.com/qemu/qemu/blob/f8b2f64e2336a28bf0d50b6ef8a7d8c013e9bcf3/hw/i2c/bcm2835_i2c.c
  BCM controller explicitly lacks repeated-start timing. `raspi3b` is a provisional
  virtual reference, not identification of the user's board.
  https://www.qemu.org/docs/master/system/arm/raspi.html
- NXP PCA9685 Rev.4, 2015-04-16 (datasheet, not redistributable source code):
  https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf
  Sections 7.3.1–7.3.5: MODE1/2, restart, PWM, ALL_LED, prescale; register AI wraps
  0x45->0 and 0xfe->0; full-off overrides full-on; prescale changes while asleep.
- Linux BCM2835 I2C combined-transfer implementation:
  https://github.com/torvalds/linux/blob/v6.12/drivers/i2c/busses/i2c-bcm2835.c
  Uses TXW interrupt to fill FIFO then program repeated start before shift completion.
- Raspberry Pi OS Bookworm Lite arm64 2025-05-13:
  https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-2025-05-13/
  Published .sha256 matches downloaded .img.xz. Kernel and DTB extracted from its
  first FAT partition. OS contains multiple licenses; VideoCore boot firmware is
  manufacturer firmware and is NOT claimed to be an entirely open source stack.
- Original Adafruit packages from https://pypi.org/ (exact wheel hashes in
  guest/requirements.lock). Source projects:
  https://github.com/adafruit/Adafruit_CircuitPython_ServoKit
  https://github.com/adafruit/Adafruit_CircuitPython_PCA9685
  https://github.com/adafruit/Adafruit_Blinka
  https://github.com/adafruit/Adafruit_Python_PureIO
  License metadata is retained in original wheel dist-info directories.
- Reuse candidate: https://github.com/bonnyr/wokwi-pca9685-custom-chip
  MIT, commit f0de752c67889c0488c5f52682ff775fa3ef14c3, 2 GitHub stars,
  last push 2023-04-24 according to live GitHub metadata. Read its actual
  src/pca9685.chip.c: Wokwi callbacks/timers and address TODOs; no drop-in QEMU
  backend. Not reused; new minimal functional model written from NXP specification.

## Selection

| Candidate | Pi-3 Linux / original libraries | Device integration | Decision |
|---|---|---|---|
| QEMU raspi3b 10.1.0 | Actual ARM Linux + matching official Pi kernel/rootfs | Real BCM I2C bus; missing PCA9685, repeated-start risk | Execute narrow model and guest test |
| Wokwi PCA9685 custom chip | Device model, not Pi Linux emulator | Wokwi-specific runtime; incomplete fields | Reviewed for reuse, not selected |
| Renode | No complete Pi-3 Linux path verified in this bounded search | Peripheral framework | Not a proven replacement for this task |

Native web search and Brave web search were both used. A bounded Brave Research
attempt returned HTTP 402 monthly quota; no budget raised. Native search found
Wokwi and QEMU source; static original sources sufficed, so no browser session used.
This is not an exhaustive simulator market survey. CAD/physics candidates remain
in the parent task; no claim about their completed integration is made here.

The CEO's subsequent source audit reports that newer Velxio documents raspi3b but
lacks I2C forwarding/network, and rpi-image-gen only formally supports native
Debian arm64 hosts. This recipe modifies a pinned official prebuilt image with
filesystem tools on x86; it is not presented as a supported rpi-image-gen build.
