# F3 method and boundaries

Exact reference: ec74b5533194d6ad2e8d75d5c8fb3831eac96446.
QA input archive SHA256:
9048acc85693b06b3ff5a41cf5d8564f7bf1de547899e6353191588dafff1bfd.
QA normal browser first attempt FAIL (seq 104–109, 0.869–1.201 s); its
successful repeat and historical F1/F2 PASS remain independent evidence.

Before testing: no threshold changes. Startup <=600 wall seconds; speed
<0.03 m/s within <=2.5 wall seconds; guest/browser 0.75 s; physics bridge 0.5 s.
Original package audit enabled in every valid full startup. No audit reuse.

Own test copy: build/ste112-f3, loopback 18095, Compose ste112-f3,
rc-pi-m3-f3-qemu and rc-pi-m3-f3-webots. Same 4+2 CPU and 2+2 GiB bounds
as QA. Existing CTO preview remains separate during diagnosis. No host,
provider, memory, browser-service or project-workspace configuration change.

Invalid setup attempt: initial container start overlapped image copy completion;
not a valid boot result. Stopped, retained preparation-overlap evidence; entire
4 GiB source/destination compared equal with cmp before the valid first start.
Slow duplicate SHA commands were stopped; they did not run during acceptance.

Valid reference normal startup: 264.826 s PASS. First unchanged original
Agent Browser helper PASS, bridge stop 1.604 s. Passive cgroup/proc measurement
is diagnostic and does not drive the vehicle. A planned four warm-run series
was cancelled after attempt 1 failed in Agent Browser open (EAGAIN after five
internal retries, before any arm/drive). This is a separate controller failure,
not the QA F3 assertion. Original console preserved. No shared browser restart.
A separate direct CDP client drove the real existing Chrome successfully;
those results explicitly name CDP rather than the original CLI helper.

Instrumented diagnostic guest: only additional guest CPU/time fields around
RX logging; same protocol/verbose echo and original libraries. Full startup
282.967 s PASS. One real CDP arm attempt failed during serial backlog. Additional
fields increase outbound size; their timing is diagnostic, not a baseline
performance claim. Original uninstrumented reference also showed serial backlog.
Guest process CPU accounting is virtual and can exceed guest monotonic deltas;
it is not host CPU time or a real Pi performance measure.

Targeted PTY regression: actual guest app, ServoKit host stub. TCOOFF stops
only outbound PTY flow while inbound drive commands remain available. The old
app blocks at its received-command print before ServoKit writes; corrected app
applies them before waiting to emit its ACK. Physics still requires an on-time
ACK and observed PWM. An earlier queue-filling fixture did not reliably block
small writes and was replaced by explicit PTY output suspension; it is not
claimed as a failing-before regression.

No original Adafruit, QEMU, kernel, device-tree, I2C/PCA model or Webots world
change. Application bytes evolve normally for M3. Browser metadata remains in
host logs; epoch+sequence associate the guest ACK and received_ns with it.
There is no separate verbose received event in the corrected guest protocol.
The actual measured PCA PWM remains the sole actuator input.

The browser helper now bounds each CLI call to 20 s (test-tool deadline only).
All attempts, including toolkit errors and aborted setup, remain in raw evidence.
Mac/Safari, remote personal browser, physical Pi/firmware/electrics and hardware
cutoff remain untested. Simulation stop is not hardware crash-safety acceptance.

Compact-protocol candidate with original multithreaded TCG: normal full start
263.781 s; four predeclared original browser/bridge-fault tests PASS (1.339,
1.342, 1.432, 1.675 s stops). Forced QEMU pause under gas PASS (1.458 s stop),
late ACK rejected, UI SICHERHEITSSTOPP with zero/disabled throttle after recovery.
However neutral raw logs still contained spontaneous 7.83 s ACK outliers.
This intermediate candidate is NOT sufficient evidence of resolved F3.
Next controlled experiment changes only the TCG host thread scheduler to single,
retaining all four virtual CPUs, full package audit and identical deadlines.

TCG single / four online CPUs: full start 261.107 s PASS; first original browser
bridge-fault run PASS (1.420 s). Neutral outlier 8.054 s remains, so single TCG
alone is rejected as an F3 fix. In its captured 8.2 s resource window the QEMU
vCPU thread ran 6.141 s and waited 0.714 s; cgroup throttling delta zero.
This rules out a claim that quota starvation accounts for that entire delay.
Next one-variable experiment adds Linux maxcpus=1 to isolate SMP behavior.
No host CPU allocation or watchdog threshold is altered.

TCG single / one online CPU: full start 221.920 s PASS, first original browser
run FAIL at arming deadline. Its record-stop also failed; original helper's
finally did not persist result. Full console and explicit recovered failure
record retained; helper now persists primary and recording errors separately.
Neutral ACKs up to 3.448 s persisted. Both CPU variants are rejected; no CPU
configuration change will be delivered on this evidence. The next diagnosis
restores ordinary four-CPU/multithread TCG, adding only a local QMP monitor to
trace UART reception after normal readiness.

UART diagnosis: default four CPUs, compact app, full startup 245.148 s. A local
QMP monitor and UART trace are diagnostic only, removed from subsequent runs.
The trace decodes input seq 412 through 427 as already read from UART DR by
Linux before ACK 412 is emitted. The 7.803 s RTT therefore is not just delayed
host socket transmission. Kernel symbols were extracted offline from the exact
unchanged compressed kernel with vmlinux-to-elf==1.2.2 in an isolated uv cache.
Register samples resolve to pl011_fifo_to_tty, IRQ handling and queued spinlocks.
One short diagnostic QMP stop captured pl011_tx_chars -> pl011_start_tx ->
uart_write -> n_tty_write -> write on CPU0; other CPUs were in idle and scheduler
work. That intentional 0.361 s VM pause is excluded from availability claims.
QMP is single-client; a separate read during its owner's capture timed out and
is a tooling ownership error, not a claimed guest stall.
The package's System.map is an 83-byte placeholder, not a usable symbol map.
The extracted embedded symbol data and complete decoder/stack evidence are
retained. Both CPU scheduler variants were rejected. Next diagnostic changes
virtual guest time to QEMU icount auto, preserving external wall-time guards.

The icount-auto probe was aborted after >120 s without a first UART boot byte;
not counted as a 600-s startup failure or a successful operating profile. Raw
ABORTED.json carries exact elapsed time. Its wait observer was terminated before
it could attribute the following comparison's startup to icount.
Next controlled comparison restores normal guest time and all four CPUs, using
existing guest chrt --fifo 1 for the application. No host scheduler setting or
external freshness/stop threshold changes. This tests the observed guest
scheduling/TTY critical path; it is not yet a diagnosed kernel root cause.

Guest FIFO priority 1: first browser PASS, stop 1.386 s; following predeclared
series stopped at attempt 1, readiness assertion FAIL before motion. Neutral
RTT reached 8.811 s; priority change is rejected and removed. The later normal
boot also took >120 s to emit initial UART text, so the aborted icount probe
does not establish an icount-specific boot defect; that comparison is inconclusive.

Direct host strace attach was denied by existing ptrace protection. No host
security change was made. Existing strace and dependencies were copied to the
isolated workspace; child tracing works without added container capabilities.
Next diagnostic launches QEMU as that tracer's child, with normal guest priority
and clock. Syscall timing is diagnostic only, not acceptance performance.

Full syscall tracing aborted after >300 s without UART boot output; intrusive
measurement, not a normal boot failure. Lightweight sendmsg-duration and host
log timing then started normally in 242.083 s. A spontaneous seq460 neutral
RTT of 6.773 s occurred, guest receive-to-ACK construction 1.525 ms, no individual
sendmsg or host log write above 50 ms. This does not exclude repeated EAGAIN
retries or guest UART scheduling; no total root cause is asserted from it.
Next comparison uses the already emulated auxiliary UART with the same app,
kernel, I2C/PCA and resource/stop limits. Its normal base DT lacks a usable
clock rate (8250 port probe -EINVAL); a separate diagnostic DT supplies an
explicit 250 MHz clock-frequency assumption. It is not a measured physical
clock or firmware-boot acceptance. Base PL011 DT and all old evidence retained.

Aux UART: first registration probe failed with -EINVAL even with the clock
property; clock-only explanation rejected. Enabling 8250.nr_uarts=1 registered
ttyS0. Reported base_baud 43750000 differs from the injected property's implied
31250000, so the clock provider superseded that property. Full startup 249.841 s,
first unchanged browser helper FAIL at readiness; neutral RTT max 6.680 s.
Aux transport is rejected. This rules out a PL011-only explanation of F3.
The comparison is retained; final code does not adopt auxiliary UART, DT clock,
port-count or guest-priority changes. Next restores original PL011/app profile
and gives icount auto/sleep-on its complete 600-s startup allowance.
