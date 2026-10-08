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
| Full SD image / normal systemd | boot-image.log, image-boot-result.json | Test in progress; not yet accepted |
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
