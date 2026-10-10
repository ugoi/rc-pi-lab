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
   **Pi 3 · Offroad Labor** tab. It is the actual shared Cloak desktop; coordinate
   before taking control. Alternatively forward privately from your computer:
   `ssh -N -L 18090:127.0.0.1:18090 agent-services`, then open that local URL.
5. Click **Start / neutral armen**, wait for ARMED, then use gas and steering.
   **STOP** or Space stops and disarms. Close/hidden tabs also request stop;
   heartbeat loss independently stops. Reopen/reconnect requires manual arming.
6. Shut down only this lab: `docker compose -f m3/compose.yaml down` (or
   `docker stop rc-pi-m3-qemu rc-pi-m3-webots` for the development containers).
   Guest is a disposable snapshot; M1/M2 originals stay unchanged.

Never edit an image while QEMU uses it. Stop the guest container before an offline
refresh; `m3/update_guest.py` refuses when a QEMU process is present in its PID
namespace. World restarts reset the world to its initial state; normal driving
never changes a pose directly. Preserve each evidence directory before retesting.

## Tests and evidence

`python3 m3/tests/test_bridge.py` tests watchdog/backpressure and PWM gating with
host fixtures, isolated from live actuator output. This is not an E2E proof.
`m3/tests/live_matrix.py --case ...` drives the running real chain via HTTP and
asserts motion/stop data. Close the UI tab or navigate it away first to release
its control lease. Fault injection needs the bridge's explicit `M3_TESTING=1`;
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

## Independent QA isolation

Use a separate checkout and separate `build/m3`/`evidence/m3` directories. Supply
known immutable M2 inputs into that checkout and prepare its own derived image.
Set `M3_GUEST_CONTAINER=rc-pi-m3-qa-qemu`,
`M3_PHYSICS_CONTAINER=rc-pi-m3-qa-webots`, `M3_PORT=18091`, and
`M3_URL=http://127.0.0.1:18091` before Compose and test helpers. Set
`M3_BROWSER_SESSION=ste114` for the browser script, preserving the existing
Cloak owner and all other tabs. The source does not require a repair or a private
replacement harness to use isolated container names/ports. To run fault cases,
export `M3_TESTING=1` before Compose; record that test configuration. This enables only named
fault-injection operations, not a different acceptance algorithm.

The raw log directory is owned by this preview. Current evidence is archived on
STE-112 before handoff. Stop the preview after review to stop CPU use and log
growth; restarting the guest preserves its previous raw PCA trace through
`m3/tests/restart_guest.py`. There is no automatic crash recovery or auto-arm.

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
