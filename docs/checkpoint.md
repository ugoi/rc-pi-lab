# STE-91 implementation checkpoint (not acceptance)

Official inputs verified: Raspberry Pi OS Lite arm64 2025-05-13 archive SHA256
62d025b9bc7ca0e1facfec74ae56ac13978b6745c58177f081d39fbb8041ed45;
QEMU 10.1.0 tarball e0517349b50ca73ebec2fa85b06050d5c463ca65c738833bd8fc1f15f180be51.
Host agent-services, isolated Docker ste91-builder, 2 CPU, 1400 MiB limit. No host change.

Model core unit tests executed successfully. QEMU model compilation and guest boot pending.
Guest rootfs is build/rootfs.img, original packages and app injected via debugfs.
Original SD archive retained; expanded base.img deliberately removed after extraction
because shared host ran out of disk (ENOSPC). Preserve source/app and rootfs.img.
Kernel8 and DTB in build/boot extracted from official image. qemu-rpi3.dtb only changes
/soc/i2c@7e804000 status to okay so far. Complete SD image still to be assembled.
Guest rc-init is a diagnostic init; it is not a final systemd deployment.

Compile: docker exec --user 1001:1001 ste91-builder /work/scripts/build-qemu.sh
Outputs: evidence/qemu-build.log and .exit; prior exit may be stale during a run.
The QEMU meson file must add pca9685.c BEFORE system_ss.add_all (fixed after first
configure failed). Pi-only config contains CONFIG_RASPI=y and uses --without-default-devices.

Next: finish compile; boot raspi3b with stock BCM controller and combined PureIO read.
Capture failure before implementing controller correction if required. Then ServoKit,
bridge reconnect, visualization, package hash audit, full image, delivery and pushed repo.
Not yet created Git repository or remote. No QA task: CEO owns separate QA.

Research: native search and Brave web ran. Wokwi MIT model found, inspected; not reused
because Wokwi runtime dependency and incomplete addressing/register semantics.
Brave Research hit HTTP 402 monthly cap after fixing minimum tokens parameter.
No provider budget change. Hindsight tools unavailable in active tool catalog.
