# Model scope

The C core models the register values used by the actual Adafruit driver and
computes steady-state PWM high/period durations from an ideal 25 MHz oscillator.
It does not toggle a simulated electrical pin on every edge. The visual servo is
an ideal kinematic indicator: 1000/1500/2000 us maps to 0/90/180 degrees, with
quantisation. This is an explicit test calibration, not measured hardware limits.

Implemented: 16 channel ON/OFF counters (wraparound), full-on/full-off precedence,
MODE1 sleep, restart flag clearing, sticky EXTCLK selection, MODE2 inversion,
ACK-vs-STOP register latching, internal prescale (minimum 3, writable asleep),
AI progression and documented wraps, ALL_LED register fan-out, power-on reset.
ServoKit reset() writes MODE1=0; that is distinct from a full power-on reset.

Boundaries: no external clock generator, OE held active, no transistor/load/current
model, no physical bus timing, oscillator stabilization delay or cycle-boundary
latching precision, no exact restart-phase synchronization. All-call/subcall
registers are stored but additional I2C addresses and general-call software reset
are not implemented; current driver disables all-call and uses device 0x40. Unknown
registers read zero/ignore writes. Live migration/savevm is unsupported.

The one-way Unix-socket bridge transports complete measured PWM snapshots including
monotonic QEMU virtual timestamp and sequence. Writes are nonblocking; slow clients
may miss frames. Consumers must reject malformed frames and reconnect to get a full
snapshot. Closing the observer does not alter PCA registers. This models a broken
visualisation link, not a safety-certified ESC failsafe. No commands bypass guest I2C.

No vehicle physics, collision acceptance, Bluetooth, camera, motor/ESC arming,
electrical safety, real Pi boot or actual Pi variant acceptance is claimed.
