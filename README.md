# Pi 3 Linux / ServoKit / virtual PCA9685

Work in progress: a real Raspberry Pi OS ARM64 guest on QEMU `raspi3b`, unmodified
original Adafruit ServoKit/PCA9685/Blinka/PureIO, Linux `/dev/i2c-1`, and a QEMU I2C
slave deriving PWM from register traffic. No application API mock.

The virtual reference is Pi 3B. The actual physical Pi-3 variant is still unknown.
See [sources](docs/sources.md), [model limits](docs/model-limits.md), and the current
[checkpoint](docs/checkpoint.md). Unit-test success is not an end-to-end result.

## Build

Use a Linux x86-64 Docker host with at least 8 GiB task disk headroom, 2 CPUs and
2 GiB RAM headroom. This is an isolated application build, not a host installation.

```sh
./scripts/fetch.sh
python3 scripts/prepare-qemu.py
docker build -t rc-pi-lab-builder .
docker run -d --name rc-pi-lab-builder --cpus 2 --memory 1400m \
  --memory-swap 1400m --pids-limit 256 -v "$PWD:/work" rc-pi-lab-builder sleep infinity
docker exec --user "$(id -u):$(id -g)" rc-pi-lab-builder /work/scripts/build-qemu.sh
```

QEMU and the OS image have fixed source hashes. The Docker base is digest-pinned;
direct Debian build packages are version-pinned and the executed toolchain inventory
is recorded. Dependency retrieval still requires those versions to remain available
in Debian repositories; this is not a claim of bit-identical rebuilds from a permanent
package mirror. QEMU's bundled Meson bootstrap uses Meson 1.8.1 and pycotap 1.3.1.

## Tests

```sh
cc -std=c11 -Wall -Wextra -Werror tests/core.c -o build/test-core
build/test-core
python3 scripts/verify-pypi.py
```

Guest provisioning, validated boot commands, measured output and deliverable image
will be documented here after execution. See `docs/checkpoint.md` for incomplete work.

## Licensing

The QEMU integration is GPL-2.0-or-later, with its standalone register core MIT as
marked in the file. QEMU and Linux remain under their upstream licenses. Original
Python wheels retain their own license metadata. The official Raspberry Pi OS image
contains separately licensed manufacturer boot firmware; this repository does not
claim an entirely open source firmware stack. NXP's datasheet is a specification
reference, not included as a relicensed work.
