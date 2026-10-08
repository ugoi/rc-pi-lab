# Pi 3 Linux / ServoKit / virtual PCA9685

Verified: a real Raspberry Pi OS ARM64 guest on QEMU `raspi3b` runs unchanged original
Adafruit ServoKit/PCA9685/Blinka/PureIO through Linux `/dev/i2c-1`. A QEMU I2C
slave derives PWM from register traffic. The visible servo uses those measured
PWM durations. There is no application API mock.

Pi 3B is the provisional virtual reference; Stefan's actual Pi-3 variant remains
unknown. See [acceptance](docs/acceptance.md), [portability](docs/portability.md),
[sources](docs/sources.md) and [model limits](docs/model-limits.md). Physical Pi,
vehicle dynamics, electrical safety, camera and Bluetooth are not validated here.

## Build and execute

Use a Linux x86-64 Docker host with at least 10 GiB task disk headroom, 4 CPUs and
2 GiB RAM headroom. No host package installation, binfmt setup or privileged
container is needed. Run these commands from a fresh checkout; never write an
image offline while its QEMU process is running.

```sh
./scripts/fetch.sh
python3 scripts/prepare-qemu.py
docker build -t rc-pi-lab-builder .
docker run -d --name rc-pi-lab-builder --cpus 4 --memory 2g \
  --memory-swap 2g --pids-limit 256 -v "$PWD:/work" rc-pi-lab-builder sleep infinity
# All following commands execute in this isolated task container.
docker exec --user "$(id -u):$(id -g)" -e JOBS=4 rc-pi-lab-builder /work/scripts/build-qemu.sh
docker exec --user "$(id -u):$(id -g)" rc-pi-lab-builder /work/scripts/extract-image.sh
docker exec --user "$(id -u):$(id -g)" rc-pi-lab-builder sh -c \
  'python3 scripts/provision.py && sh scripts/prepare-dtb.sh && sh scripts/test-core.sh'
docker exec --user "$(id -u):$(id -g)" rc-pi-lab-builder sh -c \
  'python3 scripts/verify-pypi.py && python3 tests/bridge-smoke.py && python3 scripts/run-diagnostic.py'
docker exec --user "$(id -u):$(id -g)" rc-pi-lab-builder \
  python3 tests/validate_trace.py evidence/pca-stock.jsonl evidence/boot-stock.log
# QEMU has stopped. This converts the intermediate rootfs in place into a full SD.
docker exec --user "$(id -u):$(id -g)" rc-pi-lab-builder python3 scripts/assemble-sd.py
docker exec --user "$(id -u):$(id -g)" rc-pi-lab-builder python3 scripts/run-image.py
# Optional immutable-base verification after the initial boot:
docker exec --user "$(id -u):$(id -g)" -e SNAPSHOT=1 rc-pi-lab-builder python3 scripts/run-image.py
```

The first guest run uses a diagnostic init and also executes the device matrix
and live bridge reconnect test. The second uses the complete partitioned image,
normal systemd, and the installed lab service. It powers off on success. Kernel
and modified DTB are loaded externally by QEMU in both cases. A test timeout or
failed assertion is a failure, never acceptance. Raw serial/device logs are in
`evidence/`; the harness does not send angle commands to the device or viewer.

The default execution has no network or USB camera forwarding. No socket binds
outside the checkout: the PWM bridge uses local Unix sockets only. Stop an
interactive guest cleanly from its console (`poweroff` for systemd). The bounded
test harness handles shutdown; after an interrupted diagnostic guest run,
`scripts/update-guest.py` replays/checks its filesystem before changing lab files.
Stop the builder with `docker stop rc-pi-lab-builder` when finished.

## View measured output

```sh
docker exec --user "$(id -u):$(id -g)" rc-pi-lab-builder \
  python3 scripts/render.py evidence/pca-image.jsonl build/visual
docker exec --user "$(id -u):$(id -g)" rc-pi-lab-builder \
  ffmpeg -y -f concat -safe 0 -i build/visual/frames.txt -vf fps=25 \
  -c:v libx264 -pix_fmt yuv420p build/visual/servo.mp4
```

Open `build/visual/servo-viewer.html` locally, or play the MP4. The visualisation
replays measured register states at two seconds per state, not live wall-clock
speed. Its ideal 1000–2000 µs calibration is not a measured physical servo range.
Zero/full-off and invalid pulses make no position claim.

## Reproducibility and licenses

QEMU 10.1.0 and the official Pi OS 2025-05-13 archive are SHA256-pinned. The Docker
base is digest-pinned; direct Debian build packages are version-pinned and the
executed package inventory is recorded. Retrieval requires those Debian versions
to remain available; no permanent mirror or bit-identical rebuild is promised.
The QEMU bootstrap uses Meson 1.8.1 and pycotap 1.3.1. Python wheel versions, hashes,
and upstream origins are recorded in `guest/requirements.lock` and evidence JSON.

The QEMU integration is GPL-2.0-or-later; the marked standalone register core is
MIT. QEMU, Linux and Python wheels retain their upstream licenses. The official
Pi OS image includes separately licensed manufacturer boot firmware; the whole
firmware stack is not claimed to be open source. NXP's datasheet is a specification
reference, not included as a relicensed work.

## Delivered image

The private download is `rc-pi3-ste91-20261008.img.gz` (728,439,365 bytes).
SHA256 values are in `evidence/image-sha256.txt`. Restore its raw 4-GiB container
with `gzip -dc rc-pi3-ste91-20261008.img.gz > build/rc-pi3.img`. It was cold-booted
with a temporary QEMU overlay and the base hash stayed identical. Extract the
original `kernel8.img` and `bcm2710-rpi-3-b.dtb` from the image's FAT partition
(offset 8388608), then use `scripts/prepare-dtb.sh` for the explicit virtual changes.

The first systemd boot has already initialised guest runtime state. Some ancillary
OS service starts failed/restarted in the emulator; read the acceptance report
and raw logs. This delivery proves the servo path, not general network functionality
or physical Pi boot. The actual Pi3 variant and physical calibration remain open.
