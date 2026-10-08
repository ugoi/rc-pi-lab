# Execution checkpoint — 2026-10-08

Executed in the task-owned Docker container on Agent Services. QEMU 10.1.0 is
built with the PCA9685 device; its BCM2835 controller remains byte-identical to
upstream. Raspberry Pi OS Bookworm cold boots with kernel 6.12.25+rpt-rpi-v8,
four Cortex-A53 CPUs and `/dev/i2c-1`.

The real guest verified 631 hashed files from 17 original PyPI wheels, the exact
application SHA, combined PureIO reads, ServoKit 0/90/180, invalid angle rejection,
full-off and driver reset. Its device matrix passed block reads, full-on/full-off,
ALL_LED fan-out, sleep/restart and prescale cases.

Recovered implementation findings (not hidden success claims):
- The minimal QEMU build needs OR_IRQ and UNIMP in addition to RASPI.
- The external DTB needs UART aliases and the firmware-style board revision
  0xa02082 for the original OS GPIO library. These are virtual board properties,
  not a physical inventory claim or an application shim.
- After an interrupted guest, replay the ext4 journal before debugfs writes and
  byte-verify their result. The harness now remounts read-only before termination.
- The bridge close callback initially deadlocked by re-entering the character
  backend write lock. The fix excludes writes from CLOSED and checks backend_open;
  device-only and real guest repeat executions pass. Failure logs are retained.

Full partitioned image is assembled and its systemd cold-boot test is running.
Bridge acceptance and measured video/HTML/PNG delivery have passed; image delivery
is pending. Independent QA is organised separately by the parent task owner.
No shared service, host configuration or network Pi was changed. Initial source
checkpoint is https://github.com/ugoi/rc-pi-lab/commit/9ef431b74f8d96eca81735087591b4b18e0bb665.
