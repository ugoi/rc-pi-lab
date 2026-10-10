# M3 implementation evidence — 2026-10-10

CTO implementation result, independent review assigned to STE-114. The exact
published commit, uploaded evidence archive and native report are linked on
STE-112. This is a virtual control-path/physics proof, not hardware acceptance.

## Delivered chain and model

Chrome HTTP input → host bridge → QEMU serial console `/dev/ttyAMA0` → real
Raspberry Pi 3 Linux guest → `guest_control.py` → unchanged original Adafruit
ServoKit/PCA9685 libraries → Linux I2C → unchanged M2 PCA9685 register model →
measured PWM → bridge → Webots motor/brake/servo joints and ODE contacts.
The browser cannot write Webots drive values. Watchdogs can only remove drive.
The browser canvas projects live Webots geometry; it does not run separate physics.

Baseline: `0d2da9c67db2c2b438bfc707b2396d4c424ff8ce`, no M1/M2 source modification.
Webots R2025a official Docker digest is pinned in Compose. Headless software
rendering, fixed 16-ms steps; model values and provisional boundaries are in
`parameters.json` and `CONTRACT.md`. This rigid chassis has no suspension or
validated motor-current/battery model. The 20-cm obstacle proves blocking contact,
not climbing, curb traversal or stair capability.

The actual container QEMU capability probe found neither compiled `user` network
backend nor USB NIC. Serial was selected to retain the accepted M2 binary; this
is not a universal QEMU limitation or a Pi network/Bluetooth proof.

Final normal boot audited **631 original package files, zero modified files**.
The application bytes injected into the guest are SHA-256
`df44aec2c37252c03075a760d1be2c2a0d6a9dbea1b7cc3c2c3adaa2200839be`.
Read-only extraction from the final base image confirms byte equality. The
serial audit's separate APP_SHA256 line still refers to the preserved M2 demo.
This proves the supplied application matches the image, not physical Pi execution.
QEMU binary SHA-256:
`5028732bf5272b01784e9d29acd723f9176d6f14ae21ebb16e85b8a57148d124`.
Final derived M3 rootfs SHA-256:
`e09b1ccda87c5d8b414c3cf925ca723ce493c6cff3179e8d4b1b893c490b3a33`.
M2 base image SHA-256:
`9883789a50a78e32927bfb55bafff2c2e36250fe042423d54fab3dfee2092d2f`.
The local existing QEMU binary and M2 image are distinct from QA's independent
rebuild files; do not substitute their different hashes in this report.

## Measured acceptance cases

Deadline fixed before tests: speed below **0.03 m/s within 2.5 wall seconds**.
Browser/guest freshness is 0.75 s; physics independently rejects bridge data
older than 0.5 s. Any failure latches stop; fresh driving cannot re-arm.

| Case | Implementation result |
| --- | --- |
| Straight, left/right, saturation, reverse | PASS; repeated on final normal Compose start |
| Explicit stop | 0.161 s on final motion run |
| Control link loss, throttle 0.6 | 0.809 s; fresh drive stays stopped |
| Control link loss, maximum throttle 1.0 | 0.740 s from 0.5554 m/s |
| Guest process SIGSTOP | 1.218 s; PCA still outputs 1795.84 µs |
| Guest process crash (`os._exit(77)`) | 1.236 s; PCA still outputs 1795.84 µs |
| Bridge killed and restarted | 1.025 s; old epoch rejected, explicit re-arm needed |
| Old sequence/epoch and expired arm ticket | PASS, rejected without auto-start |
| Obstacle contact | PASS; contact at obstacle face x≈1.65 m, chassis x≈1.42 m; forward movement inhibited |
| Actual browser drive/stop/orbit/zoom | PASS; vehicle moved 1.420 m and ended stopped |

Freeze, crash and bridge-kill tests used throttle 0.6; maximum-throttle stopping
was measured separately for control-link loss. Those fault runs preceded final
UI/latency instrumentation and changing the post-crash init from shell to idle
sleep. The watchdog/motor algorithm is unchanged. Independent QA must reproduce
against the exact delivered commit, including the final post-crash init behavior.

12 new host watchdog/protocol tests and 8 existing M2 host regressions pass.
These fixture checks are separate from the live chain. Syntax checks pass for
Python, shell and browser JS. The 52.8-s H.264 video decodes completely with FFmpeg.
It records real UI actions, no replay: Chrome 146.0.7680.177 on Agent Services,
Agent Browser 0.37.1, 1442×732, 15 encoded fps. The recorder captured 447 distinct
frames and duplicates frames for the constant-rate export; this is not 15 unique
rendered frames/s. Mac/Safari and remote user's playback remain untested.

## Timing and failures retained

Measured browser dispatch → guest/I2C/PWM → Webots application: **206 samples**,
median **275 ms**, p95 **455 ms**, max **639 ms**. Browser and containers share the
VM host wall clock. This includes telemetry sampling; it is neither mechanical
settling latency nor a remote-client clock or physical Pi performance claim.
Accepted guest round-trip times: 3493 samples, median 69 ms, p95 120 ms, max 629 ms.
Webots simulation/wall-time factor: 451 samples, median **0.970×**, range
0.966–0.981×. QEMU virtual nanoseconds and Webots simulation time remain separate.
The Pi TCG cold boot and package audit take several minutes.

Raw logs retain the initial failed motion run: accumulated pre-boot neutral
handshakes caused late ACKs and a fail-stop. The implementation now caps the
handshake at three attempts per connection/readiness event with nonblocking
sends. The corrected live motion run passed. Three late-ACK stop events also
remain in accepted-run epochs spanning restarts/startup; no late-ACK stop occurred
during the final successful browser recording. A first recording started during
physics reboot, stayed safely stopped, and is retained as `startup-blocked-*`.
It is not the delivered driving video. No failed evidence was relabeled PASS.

`summary.json` preserves all test filenames/results. Raw bridge, guest serial,
PCA register traces and physics telemetry carry epoch, command/PWM sequences and
clock domains. `browser-before/after.json`, browser action logs and the video
provide the actual UI evidence. Raw observations are supervisor ground truth,
not emulated physical sensor-driver evidence.

## Review runtime and limits

Private access: https://agent-desktop.tailea77a9.ts.net → **Pi 3 · Offroad Labor**
tab, or SSH tunnel and `http://127.0.0.1:18090`. Owner: CTO / STE-112. Limits and
shutdown commands are in README. Final normal Compose run disables fault hooks,
keeps the car STOPPED, and requires deliberate neutral arming. No host/NixOS
configuration or existing production service was changed. Stop the two lab
containers after review to end CPU use and log growth.

PCA PWM can remain active after a guest crash. The successful emergency stops
are independent **simulation brakes**, not a proven physical shutdown circuit.
Real ESC/servo calibration, hardware cutoff, electrical limits, suspension,
terrain/climbing behavior and full-car safety remain outside this delivery.
