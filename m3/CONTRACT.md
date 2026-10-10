# M3 execution contract (set before live tests)

Webots R2025a, 16 ms fixed physics steps, ODE wheel joints/contact physics.
Simulation time is Webots seconds; QEMU `ns` is its own virtual clock. Neither is
assumed equal to host wall time. Host `monotonic_ns` correlates browser command,
serial transmission, guest ACK and observed PCA frames. Browser sequence/bridge
UUID and PCA sequence are separate monotonic domains. All JSON physical values
use metres, seconds, radians, Nm and microseconds as named. Physics telemetry is
supervisor ground truth, not a physical sensor driver.

Before testing: browser and guest freshness 0.75 wall seconds; Webots independently
rejects bridge actuator files older than 0.5 wall seconds. Failure latches STOPPED.
At each physics step brakes replace drive after invalidation. At the configured
maximum 0.56 m/s, the measured flat-ground speed must drop below 0.03 m/s within
2.5 wall seconds from stop/failure. If simulation stalls, no physical-time
assurance is claimed. Physics resumes with brakes; the measured factor is shown.
An obstacle test must show contact and inhibited forward motion, not teleportation.

Arm requires explicit browser action with zero controls, original-library neutral
PWM plus fresh guest ACK, and 0.6 s dwell. After stop/disconnect/restart, fresh drive
messages cannot arm. Epoch changes on bridge restart. Old epochs and non-increasing
browser/PCA/guest sequences are rejected. Every browser command also consumes a
one-use server ticket expiring after 0.75 wall seconds, preventing delayed
new-sequence commands and replayed arm requests from starting the car. Per-client
sequence history survives lease transfers within the bridge epoch. A sole browser lease prevents two drivers.
Throttle and steering saturate to [-1,1]. Assumed ESC calibration: 1000/1500/2000 us,
±20-us throttle deadband (0.04 normalized), bidirectional drive, reverse first brakes to rest with
0.3 simulation-second dwell. These are assumptions, not the real 60-A ESC's facts.
No transmission torque/speed validation against the physical motor is claimed.

The guest watchdog requests neutral after 0.6 guest seconds. Crucially, that alone
cannot stop after SIGSTOP/crash. The independent Webots watchdog applies a simulated
brake even while PCA9685 holds its last pulse. Real hardware needs an independently
powered/clocked enable/cutoff design, verification, and calibrated stopping distances.
There is no physical safety acceptance here.

Parameterized chassis is a rigid 2-kg box, 0.44 x 0.24 x 0.10 m, four 0.12-kg wheels,
radius .07 m, wheelbase .32 m, track .32 m. Principal chassis inertia follows the
box formula; COM is provisionally .01 m below its origin. Tire friction is 1.0;
no suspension or tire deformation. Steering limited to .48 rad, 1.5 rad/s and 1 Nm;
wheel limit 8 rad/s, 12 rad/s² and .35 Nm. Equivalent 20:1 reduction is descriptive
for future motor mapping; wheel-side limits drive the model. Parameter validity:
positive finite dimensions/masses, fixed ratio assumptions; this is one tested
parameter set, no certification across arbitrary substitutions or curb/stair sizes.

## Deliberate limits and failure policy

Only the checked-in parameter set is runtime-accepted. Generator input guards:
chassis dimensions 0.1–1.5 m, chassis mass 0.1–20 kg, wheel radius 0.02–0.3 m,
positive wheel width/mass, wheelbase below chassis length, track above chassis
width, friction 0.1–2, steering angle 0.05–0.6 rad, timestep 1–32 ms. These are
software input limits, not physical design recommendations. Wheel torque and
speed limits are wheel-side; no validated motor-current or battery model exists.

The serial startup handshake retries at most three times per connection/readiness event, at most once a wall second, always neutral,
with an initial newline to recover from pre-boot console fragments. Pending
writes are bounded and use nonblocking sends; backpressure disarms. Physics
telemetry loss also latches the bridge. The shared desktop is an access path,
not a test of the user's Mac/Safari client.
