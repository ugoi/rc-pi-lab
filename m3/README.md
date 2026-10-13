# M3: slow 4x4 with Pi/Linux, original Adafruit and Webots

All controls travel through the Pi guest. The Webots controller accepts only
validated PWM observations from the bridge, plus a separate fail-stop gate.
The canvas is a live projected view of Webots supervisor geometry. It does not
compute vehicle physics and is not a replay. Drag to orbit; wheel to zoom.

Read [the acceptance contract](CONTRACT.md) before testing. Model assumptions
and deadline values are in `parameters.json`. No physical car, Mac Safari,
Bluetooth or guest network acceptance is implied.

## Start and stop

Owner: CTO / STE-112. This is an isolated application preview on Agent Services
VM202, not a boot-enabled host service. Bounds: guest/bridge 4 CPUs + 2 GiB,
Webots 2 CPUs + 2 GiB, no additional swap, 256 PIDs each. Software rendering;
no GPU reservation. Containers remain running for human review until explicitly
stopped. No host rebuild, production-service restart or public listener.

1. Follow the repository M2 build/extract/provision instructions through creation
   of a diagnostic rootfs (before `assemble-sd.py`). Original package/image/QEMU
   pins apply. Build image name: `rc-pi-lab-builder`.
2. Create `build/m3` and `evidence/m3`. In the existing builder container run
   `python3 m3/prepare_guest.py`. It creates a separate sparse M3 rootfs and
   verifies app bytes. Set `M3_BASE_IMAGE=build/rootfs.img` for a fresh M2 build;
   the local historical default is `build/qa-fixes-work/build/rootfs.img`.
3. `python3 m3/generate_world.py`; `docker compose -f m3/compose.yaml up -d`.
   Initial Pi TCG boot/package audit takes several minutes. Start stays blocked
   until neutral PWM and fresh guest ACKs exist. Check `evidence/m3/serial.log`.
4. Open `http://127.0.0.1:18090` on Agent Services. For the existing private browser,
   open https://agent-desktop.tailea77a9.ts.net through Tailscale and select the
   **Pi 3 · Offroad Labor** tab (review runtime `127.0.0.1:18094`, Compose
   project `ste112-fix`; a fresh default setup above uses 18090). It is the actual shared Cloak desktop; coordinate
   before taking control. Alternatively forward privately from your computer:
   `ssh -N -L 18090:127.0.0.1:18090 agent-services`, then open that local URL.
5. Click **Start / neutral armen**, wait for **FAHRBEREIT**, then use gas and steering.
   **STOP** or Space stops and disarms. The controlling tab requests stop when hidden;
   heartbeat loss independently stops. Reopen/reconnect requires manual arming.
6. Shut down a fresh default lab: `docker compose -f m3/compose.yaml down`.
   The published review uses project `ste112-fix`: stop it explicitly with
   `docker stop rc-pi-m3-fix-qemu rc-pi-m3-fix-webots` in any directory.
   Guest is a disposable snapshot; M1/M2 originals stay unchanged.

Never edit an image while QEMU uses it. Stop the guest container before an offline
refresh; `m3/update_guest.py` refuses when a QEMU process is present in its PID
namespace. World restarts reset the world to its initial state; normal driving
never changes a pose directly. Preserve each evidence directory before retesting.

## Tests and evidence

`python3 m3/tests/test_bridge.py` tests watchdog/backpressure and PWM gating with
host fixtures, isolated from live actuator output. This is not an E2E proof.
`m3/tests/live_matrix.py --case ...` drives the running real chain via HTTP and
asserts motion/stop data. A stopped vehicle is claimed only by an explicit neutral arm. Idle viewer tabs
do not renew a lease. Unarmed/non-owner drive requests are rejected with HTTP409. Fault injection needs the bridge's explicit `M3_TESTING=1`;
the standard compose runtime disables this HTTP operation. Guest fault hooks additionally require `M3_TESTING=1` at QEMU launch;
normal startup leaves both gates disabled. After the first complete package
audit, repeat fault-test boots of the exact unchanged base may use
`M3_REUSE_AUDIT=1`; the serial log explicitly marks this evidence reuse.

Raw `pca.jsonl` is the actual unchanged PCA9685 model trace. Bridge logs correlate
browser client/sequence -> serial sequence/epoch -> guest ACK -> device sequence.
Physics logs include joint angles, poses, contact points, speed, simulation factor
and the exact accepted actuator-source IDs. QEMU/guest clocks are not treated as
host wall clocks. See the delivered task report for measured results and limits.

## Upstream references

- [Official Webots Docker/headless usage](https://github.com/cyberbotics/webots/blob/R2025a/docs/guide/installation-procedure.md)
- [Webots Hinge2Joint](https://www.cyberbotics.com/doc/reference/hinge2joint?version=R2025a)
- [Cylinder axis and geometry](https://www.cyberbotics.com/doc/reference/cylinder?version=R2025a)
- [QEMU Raspberry Pi models](https://www.qemu.org/docs/master/system/arm/raspi.html)

The actual existing QEMU build was probed in its container: no USB NIC device or
slirp `user` backend is compiled. Other QEMU builds can provide USB networking;
this implementation chooses serial to preserve the accepted M2 device build.
This is a build-specific capability finding, not a claim that Pi networking is
impossible in QEMU. Raw output: `evidence/m3/network-capabilities.txt`.
During F3 diagnosis a separate QEMU build with USB networking and Slirp did run
Linux TCP end to end, but still reproduced availability failures. That prototype
and its measurements are archived; the delivered runtime retains the original
UART/device build. Neither experiment proves physical Pi networking/Bluetooth.

## Independent QA isolation

Use a separate checkout and separate `build/m3`/`evidence/m3` directories. Supply
known immutable M2 inputs into that checkout and prepare its own derived image.
Set `M3_GUEST_CONTAINER=rc-pi-m3-qa-qemu`,
`M3_PHYSICS_CONTAINER=rc-pi-m3-qa-webots`, `M3_PORT=18091`, and
`M3_URL=http://127.0.0.1:18091` before Compose and test helpers. Use a separate Compose project as well:
`docker compose -p ste114 -f m3/compose.yaml up -d` (and the same `-p ste114`
when stopping). Container names alone do not isolate Compose project ownership. Set
`M3_BROWSER_SESSION=ste114` for the browser script, preserving the existing
Cloak owner and all other tabs. The source does not require a repair or a private
replacement harness to use isolated container names/ports. To run fault cases,
export `M3_TESTING=1` before Compose; record that test configuration. This enables only named
fault-injection operations, not a different acceptance algorithm.

The raw log directory is owned by this preview. Current evidence is archived on
STE-112 before handoff. Stop the preview after review to stop CPU use and log
growth; restarting the guest preserves its previous raw PCA trace through
`m3/tests/restart_guest.py`. This helper stops/restarts the whole guest/bridge
Compose container, preserves its fault/audit configuration and requires a new
bridge epoch with fresh neutral ACKs. It does not assume an always-running
development shell. There is no automatic crash recovery or auto-arm.

## Latency interpretation

The browser timestamps command dispatch with `Date.now()`. The bridge correlates
it with its guest sequence/ACK and the PCA device sequence; the physics sample
retains that source plus its wall-clock timestamp. The delivered browser runs on
the same VM as the containers, so these real-time clocks share one host. This
measures browser dispatch → HTTP → serial guest → original I2C/PWM → Webots motor
application (including trace sampling); it is not a remote browser's clock-sync
claim, a physical Pi benchmark, or the servo's complete mechanical settling time.
`python3 m3/summarize.py` reports those samples separately from accepted guest
round-trip times and Webots simulation/wall-time factor. Safety deadlines use
monotonic clocks regardless of wall-clock adjustment.

## F1/F2 corrections (STE-112, 2026-10-12)

During Pi boot the bridge now **waits for guest readiness before any handshake**.
Pre-boot host input could leave the emulated PL011 receive FIFO full during the
Linux driver's bounded startup drain. The guest announces readiness after raw
UART setup and neutral I2C writes, repeating it while disarmed so a replacement
bridge can connect. These beacons do not count as fresh command ACKs. All three
maximum Hello attempts share one host-wall-time spacing gate (at least 1 s).
No retries until success or manual console priming are part of the start path.

The page displays **PI STARTET**, **VERBINDUNG WIRD GEPRÜFT**, **GESTOPPT** and
**FAHRBEREIT**, with German timeout/disconnection explanations. Start is enabled
only with fresh guest/PWM and physics data. A failed HTTP connection clears the
active display and controls; it does not pretend to know the current vehicle
speed. Webots independently records current `mode`, `reason`, `source_status`.
`source` remains the historical input for correlation, including stale ARMED
commands. Bridge expiry reports `STOPPED / bridge_timeout / stale`; reversal
braking cannot overwrite that fault reason. The unchanged physics watchdog is
still simulation-only.

Additional targeted checks (host tests are not live I2C evidence):

```sh
python3 m3/tests/test_bridge.py
python3 m3/tests/test_actuator_state.py
python3 m3/tests/test_guest_handshake.py  # actual app protocol via PTY, ServoKit stub
node m3/tests/test_status.cjs
python3 m3/tests/wait_ready.py           # one real startup, 600 s maximum
python3 m3/tests/browser_bridge_fault.py # actual browser gas, SIGKILL bridge, recovery
# Fault runtime only: export M3_TESTING=1 before compose up.
python3 m3/tests/live_matrix.py --case freeze --drive-throttle 1
python3 m3/tests/restart_guest.py
python3 m3/tests/reset_world.py
python3 m3/tests/live_matrix.py --case crash --drive-throttle 1
python3 m3/tests/idle_after_crash.py      # 60 s, exit 77 and idle PID1 marker
python3 m3/tests/restart_guest.py
```

Set the documented `M3_URL`, container names and `M3_BROWSER_SESSION` for your
isolated QA checkout. Release the own browser tab to `about:blank` before HTTP
matrix cases. `restart_bridge.py` and the browser fault helper preserve the
container's configured fault gate. A guest crash emits `M3_APP_EXIT code=77` then
`M3_IDLE_INIT`; init keeps Linux alive without a shell, auto-restart or auto-arm.
Every successful full restart must show a new epoch, fresh neutral ACK and PWM.
See `m3/results/qa-fixes-20261012` and the native correction report for all attempts,
source diagnosis, delivered pins, raw evidence and the independent QA boundary.

### Isolated browser acceptance client (F3 investigation)

`python3 m3/tests/browser_bridge_fault.py` and `browser_guest_pause.py` attach
to existing Cloak Chrome CDP9222 using Node's native WebSocket. Each test creates
and disposes its own browser context, sends real mouse/key events, and records
actual Page.startScreencast JPEG frames with timestamps. FFmpeg pads odd sizes
to even pixels and encodes with one thread. The shell CLI probe reports Node22.23.2; the actual privileged test child
resolves Node24.19.0. The live runs used that Node24.19.0 child and FFmpeg.
Set M3_URL and M3_GUEST_CONTAINER for the owned lab. M3_BROWSER_TARGET is an
optional explicit already-owned CDP target; tests never fall back to other tabs.
No Chrome service/profile restart, provider login, or test input through /command
is performed by this browser driver. Prior Agent Browser failures are retained.
The first failed attempt is not erased by a subsequent helper fix.

### F3: immutable guest filesystem during control

The M3 root filesystem boots read-only. Init verifies that mount mode, puts
`/run` and `/tmp` in guest RAM (`/tmp` limit 32 MiB), and disables Python bytecode
cache writes. Its working directory is `/run/rc-control`: the original lgpio
package requires a writable directory for its notification FIFO. The control application and original Adafruit files are unchanged
by this operating profile. Persistent guest SD writes are outside the supported
active-driving profile: QEMU 10.1.0's emulated SD write path produced long stalls
during diagnosis. Logs remain on the host through the existing bridges. Root
image preparation/update still runs offline while its own QEMU is stopped.
This is an emulation constraint, not a measurement of physical Pi SD performance.
Watchdog and stop deadlines remain unchanged; no warmup/retry grants readiness.
