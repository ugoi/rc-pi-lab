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

Full partitioned image and normal systemd service cold boots have passed. The final
QEMU snapshot run left the delivered raw image unchanged (SHA before/after match).
Bridge, register and original package acceptance pass. Video, HTML and PNG were
uploaded to Paperclip and downloaded again with matching SHA256. The image is
728,439,365-byte gzip with full decompression/hash validation; private Nextcloud
upload and full readback have passed with the exact compressed SHA256. The final disposition and reviewer are recorded on the Paperclip task. Independent QA is organised
separately by the parent task owner. See acceptance.md for OS service limitations.
No shared service, host configuration or network Pi was changed. Initial source
checkpoint is https://github.com/ugoi/rc-pi-lab/commit/9ef431b74f8d96eca81735087591b4b18e0bb665.

The shared filesystem again returned ENOSPC during xz compression. Only this task's
incomplete output and reproducible input/source caches were removed. The raw image,
QEMU binary, package wheels, source, and raw evidence remain. Final gzip compression
used existing RAM-backed temporary storage, removed after verified cloud
delivery; no new mount or infrastructure change was made.

The task container was stopped after the guest tests (no running QEMU remains).
Its idle PID1 needed Docker's final stop signal. Both full-image acceptance runs
had already exited 0 after orderly poweroff; diagnostic acceptance had remounted
its filesystem read-only. The raw image is retained.
