# Acceptance — virtual Pi3 vertical proof

Executed on 2026-10-08, not inferred from source code. Independent QA is organised
separately by the parent task owner; these are CTO execution results.

| Layer | Evidence | Result |
|---|---|---|
| Register/PWM core | C assertions, undefined-behavior sanitizer | PASS: reset, prescale, AI/wrap, ON/OFF, full-on/off, ALL_LED, sleep/restart, MODE2 |
| Original packages | PyPI release hashes; guest RECORD audit | PASS: 17 exact wheels; 631 files checked, zero modifications |
| Application identity | Guest SHA matches repository source | PASS: `5727aa31318c78505b1556966b46314941417037920c400a61edb1bc47f6a9d4` |
| Pi machine cold boot | boot-stock.log, uname, distro, CPU/model, device | PASS: Pi3B, four Cortex-A53, Linux 6.12.25+rpt-rpi-v8, Bookworm, /dev/i2c-1 |
| Linux combined reads | Original PureIO I2C_RDWR, original PCA frequency reads | PASS functionally; upstream controller inserts STOP, see model limits |
| Original ServoKit | 0/90/180; -1/181 rejected; None; driver reset | PASS |
| Device correlation | pca-stock.jsonl + guest-trace-result.json | PASS: 995.52 / 1498.16 / 1995.92 us, period 19988.48 us |
| Guest device matrix | Original PureIO block reads and writes | PASS: full-on, full-off precedence, ALL_LED, sleep/restart, prescale |
| Bridge device regression | Paused QEMU, three close/reconnect cycles, QMP responsiveness | PASS; distinct from guest evidence |
| Bridge during guest app | bridge-test.json, second unmodified app run | PASS: 995.52 before disconnect; fresh 1498.16 snapshot; 1995.92 and zero afterwards |
| Visible servo | PNG, MP4, self-contained interactive HTML from trace | Produced and uploaded; PNG inspected, H.264/800x520/25fps video verified |
| Full SD image / normal systemd | boot-image.log, image-boot-result.json | PASS: first boot, then immutable-base cold boot; service and poweroff succeed |
| Physical Pi | Actual board variant, real firmware/SD boot, actual I2C/servo | NOT TESTED |

Diagnostic cold boot through the first APP_PASS took 220.64 seconds on this shared
x86 host in the 4-CPU/2-GiB task container. This is one observed run, not Pi3 hardware
performance or a latency benchmark. The 40-second video uses two seconds per
selected register state; it is an evidence replay, not a real-time recording.

The ideal 1000–2000 us calibration maps to 0–180 degrees with 12-bit PWM
quantisation. No measured hardware range, torque, inertia or electrical model is
claimed. Power-on model reset and ServoKit's MODE1-only driver reset are distinct.

The bridge initially deadlocked at socket close; the callback no longer writes
while under the chardev write lock. Both device-only and actual-guest retests pass.
A diagnostic cleanup command initially used the physical PARTUUID from fstab;
explicitly naming /dev/mmcblk0 completed the read-only remount (DISK_CLEAN=0),
and the offline filesystem check passed before SD assembly. Raw logs retain this.

App identity, root filesystem identity and SD boot equivalence are separate:
see [portability](portability.md). This is not the completion of vehicle physics,
CAD, electrical power validation, network control, real Bluetooth or camera work.

The first full systemd run took 750.42 seconds through poweroff. It showed initial
failures for polkit, logind and NetworkManager and dependent ModemManager/network
wait units; logind and NetworkManager subsequently started. These are preserved
in `boot-image-first.log`. Overall OS service health is separate from the passed
Adafruit service. Networking, login management and modem functionality are not
accepted by a successful servo trace.

The final cold boot with QEMU `-snapshot` passed in 802.07 seconds through shutdown
and checksum readback. Base-image SHA256 before and after is identical:
`8bd3e452033e0fb97b9432b823990a03b5956409f2836a8785983c867d57b40c`.
The unchanged base image is the delivered raw image. This still uses an external
kernel/modified DTB and does not prove real firmware boot. The final log retains
an initial NetworkManager failure and dependent wait-online failure; NetworkManager
then starts. General network/modem/client acceptance remains out of this proof.

The gzip artifact is 728,439,365 bytes. Decompressing it yields exactly
4,294,967,296 bytes and the tested raw SHA256; gzip CRC validation also passed.
All timing above describes this shared x86 emulation host and this run only.
