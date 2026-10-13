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

Complete icount allowance: startup 335.889 s PASS; first original CLI helper
failed at open timeout before input. Neutral RTT independently reached 9.250 s.
This clock variant is rejected. Resource window: 8.812 CPU-s in 9.330 wall-s,
zero cgroup throttling; this does not establish absence of host contention.

Ordinary PL011 lock/retry diagnostic: startup 289.143 s. ACK seq101 took
6.640552 s, receive-to-ACK construction 15.066 ms. No >50 ms shared-lock record
overlapped [26008864637491,26015505189443] host monotonic ns; no sendmsg retry
series was recorded. Other boot windows did contain up to 2.680 s lock holds,
so the experiment does not claim globally zero host stalls. First CLI open
again timed out; no drive assertion ran. The full data remains preserved.

Rejected binary/base64 UART frame experiment: startup 255.723 s, typical ACKs
became shorter (median about 36 ms), but seq195 still took 7.995908 s. No frame
codec will be delivered as an F3 fix. Prototype and raw frames are archived;
application protocol restored to e8b1885 JSON without accepting old late ACKs.
Its first new-CDP browser attempt also failed before arming: a visible old own
tab renewed an idle control lease, rejecting the new arm. The independent
long neutral ACK remains a separate availability failure. Original failed video
encode (odd 1279-pixel width) and source frames preserved; encoder now pads to
even dimensions, without changing the scene or input record.

Browser boundary: old own tab's Page.enable timed out through direct CDP too.
A new isolated browser context succeeded. Three own Agent Browser daemons were
identified by exact session environment and PID (ste112-f3, ste112-f3-final,
ste112-f3-bound) and terminated without signalling the shared browser. Old own
tabs/context were closed by exact CDP id; unrelated tabs and public 18094 preview
preserved. Updated test helper uses real mouse/key CDP events in a separate
owned context, actual Page.startScreencast frames/timestamps and FFmpeg. Contexts
are disposed after each test. Existing CLI failures are not reclassified as
successful runs. UI idle spectators no longer acquire a lease; explicit neutral
arming claims a stopped vehicle. Owner heartbeat and global explicit STOP stay.

Network comparison preparation (not a live acceptance result): exact QEMU10.1
source, same PCA model plus CONFIG_USB_NETWORK and system Slirp4.8.0-1+deb13u1
in an isolated builder image. Build bounded to2CPUs/2GiB. Kernel/rootfs already
contain cdc_ether/rndis_host and iproute tooling. TCP adapter runs identical
Adafruit app bytes as a child. Clean EOF can accept a new neutral child; a crash
terminates the listener. A real loopback test with ServoKit stub verifies this
boundary; it is not Pi/I2C evidence. No host package/service change.

Before network live testing, official QEMU10.1 functional Pi2/Pi4 Linux tests
show dwc_otg.fiq_fsm_enable=0; baseline guest log explicitly enables FIQ FSM.
The network build is paused to avoid measurement load. Next controlled run
changes only that guest boot parameter on original QEMU/UART/kernel/DT, with
full package audit and unchanged external deadlines. Improved browser isolation
and idle-lease handling apply to the test harness/UI, not guest serial timing.
No causal conclusion about FIQ is made before that comparison.

FIQ-FSM-off UART comparison: full startup 255.023 s PASS. First actual CDP
browser drive/bridge kill PASS, stop1.144 s. Predeclared six-run followup stopped
at run1: drive and kill stop1.204 s, but post-reconnect status SAFETY STOP rather
than normal STOPPED. Neutral RTT2.266 s confirms F3 remains. FIQ-FSM-off alone
is not a solution. Both real browser videos encoded and checked; source frames
and timing metadata identify them as live captures. QEMU network build resumed
only after shutting down the comparison. Subsequent video encoding explicitly
uses one codec/filter thread to bound test-artifact CPU load; no app deadline
or late-ACK acceptance changes.

Network prototype build completed with exit0. QEMU SHA256
cbdfa9f9599522c1ef91b40be1d38c883331c6f268abd80cbfaf9c1ab9dad449.
Runtime device/backend help confirms usb-net and user. Initial help probe without
-M raspi3b failed before any guest launch; corrected probe and raw error retained.
First full network boot starts with all631 package files audited and fault hooks
disabled. The predeclared first real browser fault test and six-run followup
retain original watchdog, arming, speed and restart assertions.

Network prototype1 (exec per connection): full startup275.248 s PASS with
Linux cdc_ether/eth0 and all631 original package files unchanged. First actual
browser drive reached speed threshold; bridge-SIGKILL stop1.128 s and correct
disconnected UI. Overall first browser FAIL at the unchanged10 s reconnect
readiness deadline: a new interpreter repeated Adafruit imports on every
connection. New connection did eventually emit ready, but that is not a PASS.
Six-run series not executed after the first failure. Raw trace/video archived
under network-first-child-exec. First48 ACK samples all below750 ms, maximum
502.177 ms; this short sample alone does not establish reliable availability.

Prototype2 preloads imports before listen, then forks a new process per
connection. The listener itself never constructs ServoKit/opens I2C; unchanged
application constructs its own instance and writes neutral in each child.
Clean EOF accepts a new neutral process; crash77 still terminates listener.
Local actual-app/ServoKit-stub lifecycle test PASS (not Pi/I2C evidence).
Full-audit normal Pi boot and original first/followup assertions now run.

Network prototype2/four active Linux CPUs: full start300.782 s PASS, first
browser FAIL before motion. seq33 RTT1.247159536 s (received-to-ACK19.279 ms),
seq34 .798113232 s. Therefore changing UART to TCP alone does not resolve F3,
and UART is not established as the sole cause. Resource window1.370 s: QEMU
cgroup1.640 CPU s, no quota throttling; busiest vCPU .854 run/.204 wait seconds.
Host CPU pressure was about25% some/0% full; those observations alone are not a
causal host-load finding. Full first failure/video and rejected ACKs preserved.
Next controlled comparison changes only Linux maxcpus=1, keeping original
MTTCG/four exposed Pi3 hardware cores, network/preload prototype and deadlines.
No watchdog extension, priority change or host CPU-affinity change.

Network/maxcpus1/MTTCG diagnostic aborted at472.337 s,
before its600 s deadline, after live Docker statistics showed407.52% CPU
for the guest/bridge container. No completed startup verdict is claimed.
All in-memory readiness observations were saved through SIGINT/finally before
stopping; ABORT.json records that this is manual resource rejection, not a
600 s timeout. Raw data under network-one-mttcg-aborted.

Exact QEMU10.1 source explains why this attempted reduction is unsuitable:
hw/arm/raspi.c:159 parks unused secondary CPUs in a WFE/spin-table loop.
target/arm/tcg/translate-a64.c:1948 trans_WFE does not yield in CF_PARALLEL
(MTTCG); the source explicitly documents busy spinning. This is a cause of
this diagnostic's resource increase, not proof of the original F3 cause.
Next comparison uses tcg,thread=single so WFE yields via op_helper.c:472,
with the same Linux maxcpus1/network/app image. Existing watchdogs unchanged.

Network/maxcpus1/single-TCG: FAIL at full600 s start deadline, no guest
readiness. Source flags and full package audit are retained; no browser trial
was possible. Diagnostic variant rejected, not a fix. Subsequent diagnostic
returns to four Linux CPUs and MTTCG, adds select-duration and previous-ACK
flush timing to the guest ACK, and enables bounded QMP stack captures.
All QMP VM pauses are explicitly marked and excluded from acceptance. This
diagnostic explicitly reuses the prior full631-file unchanged-library audit
(m3.reuse_audit=1 is visible in boot log); it is not a normal-start acceptance.

UART CPU/IRQ affinity diagnostic: application restricted to guest CPU0 and
irqaffinity=0; four Linux CPUs remain online. Explicit audit reuse, so startup
173.564 s is diagnostic, not a new full-audit acceptance result. First browser
bridge-fault PASS (1.063 s), first of six planned followups PASS (1.134 s), second
FAIL at disabled arm control. Neutral RTT reached 7.691 s; the affinity change
is rejected. All attempts, videos and prototype source retained. The following
probe restores ordinary CPU/IRQ affinity and uses running QMP register samples
(no deliberate stop/cont) to locate the active guest instructions during a stall.
Any monitor overhead remains diagnostic and is excluded from acceptance.

Running QMP PC samples took appreciable monitor time during a spontaneous early
lag. The 12-s capture is diagnostic only, not unperturbed latency. It shows
changing timer/TTY/locking and user-code PCs rather than one proved tight loop.
A following 90-s and then bounded 300-s host perf_event CPU sample (199 Hz per
QEMU thread, user space only) contained zero late-ACK intervals. Consequently
these are normal-running references, not a root-cause profile. Sampling in the
container was denied by its existing seccomp; the existing host read-only perf
interface (-1 policy) permitted sampling the exact own-process PID. No seccomp,
capability or host policy was changed.

The next guest phase-time diagnostic wraps read/select/JSON/output and observes
GC duration, while host CPU sampling starts at readiness. Its launch script
intended to remove audit reuse but a whitespace mismatch left the explicit
m3.reuse_audit=1 flag present. The live command was checked; this attempt is
therefore audit-reuse diagnostic only, never a full-audit normal-start PASS.

Phase/CPU diagnosis: readiness 170.089 s (explicit audit reuse). An early lag
triggered bounded perf sampling. Of 3,843 user-space CPU samples, 1,185 overlap
late ACK intervals. SD write functions and their block/coroutine path appear
heavily in these intervals: bcm2835_sdhost_fifo_run, sd_write_byte,
bdrv_co_is_inserted, blk_is_inserted and qemu_aio_coroutine_enter. Guest phase
records show select/print delays; no long GC callback was recorded. This points
to emulated SD I/O affecting the whole guest, not a UART-only transport defect.
The sampler resolver initially lacked its symbol-file copy; it was rerun with
the unchanged exact QEMU binary's symbol table. Raw samples were preserved.

First RO-only candidate: original app fails importing unchanged lgpio because
its notification FIFO cannot be created in readonly cwd (`.lgd-nfy-3`). App exit1
is preserved and observation ended early; not misreported as a 600-s timeout.
The coherent final profile uses readonly root, 32MiB tmpfs /tmp, cwd
/run/rc-control on tmpfs, and PYTHONDONTWRITEBYTECODE=1. Init fails if root is not
read-only. Libraries/application code remain unchanged from e8.

RO/RAM profile normal full-audit start 194.970 s PASS, original 631 package files
verified. First actual browser/bridge-fault PASS (1.332 s stop), followed by all
six predeclared browser attempts PASS: 1.134, 1.153, 1.247, 1.157, 1.151,
1.298 s. No retries or priming. Across 2,170 correlated ACKs, zero >0.75s;
max 0.184225s, p95 0.080943s, median 0.036431s. Guest/browser/physics deadlines
unchanged. This first profile comparison used builder-net (extra Slirp packages,
original UART QEMU binary); the final fault/restart and preview runs return to
the original builder image, with exact file/image evidence.

Controlled 2MiB SD/RAM write comparison setup initially passed noatime as
rootflags; ext4 rejected that filesystem-specific parameter and kernel panic
preceded init. Invalid diagnostic setup is retained, observation ended early,
not a 600-s result or F3 regression. Corrected setup applies remount,noatime in
init for the RW diagnostic. This comparison explicitly reuses the prior package
audit and wraps the unchanged guest app to perform one bounded temporary write.
It is diagnostic only and not the delivered normal startup.

Second storage-comparison setup: target-only `mount -o remount,noatime /`
consulted the image's historical fstab PARTUUID, absent from the extracted root
block image, and init exited4. Retained as invalid diagnostic setup; no normal
profile or write-probe result. The controlled RW diagnostic now passes explicit
`/dev/mmcblk0 /` source and target. The delivered RO profile uses no remount.

First successful RW probe boot 167.712 s (audit reuse). Its temporary 2MiB
write+fsync reported 8.139s guest time, but diagnostic-thread print fragments
interleaved with two ACK lines. This is retained as diagnostic framing failure,
not the clean causal comparison. The helper now serializes whole output lines
identically in both profiles; a host-only test deliberately interleaved 200
body/newline calls and recovered 200 separate valid JSON frames. No original
control-app or Adafruit source changed for this diagnostic wrapper.

Clean storage comparison (diagnostic audit reuse, identical 2MiB temporary
write+fsync wrapper, control app unchanged): RW-SD readiness166.698s,
write8.328481s guest / markers8.461606s host, SD writes2,142,208bytes,
15 late ACKs of154, max7.498172s. RO-RAM readiness168.924s,
write0.169284s guest, zero SD writes, zero late ACKs of874, max0.405125s
(includes hello). The pair runner exited127 after both probes completed, reporting
`ls/observe_storage.py: No such file or directory` at line34 (the saved file
has `done` there). The runner read failure was not independently isolated;
both completed marker/sample files and latency analysis are retained. No
probe repetition was used to manufacture PASS.
This experimentally reproduces and removes the emulated SD-write contention
identified by the independent CPU profile. Individual background write
producers (atime, bytecode, notification FIFO) were not separately traced;
no claim is made that one specific file was solely responsible for QA seq104–109.
The original QA timestamps demonstrate the same delayed guest service/return
symptom, while the causal mechanism is established by our instrumented run.

Final original-builder regression: full-audit first start206.683s PASS; actual
browser/QEMU-SIGSTOP stop1.539629s with late ACK rejection, UI zero/disabled,
SICHERHEITSSTOPP; stale commands PASS; browser disconnect at0.555430m/s
stop0.792565s; app crash at0.555430m/s stop1.315583s while PWM held1995.92us;
60.230863s durable idle PASS; full guest/bridge restart197.032599s with new
neutral epoch PASS; first subsequent browser drive/bridge-SIGKILL PASS1.111634s,
current bridge_timeout / disconnected UI then GESTOPPT after fresh reconnect.
No test retries. All34 executed code/config files match the final source;
only evidence/documentation was extended after execution. Original builder
image sha256:577fb654ac55a89333e6a3b9dbd7e85d1ce8995c8cde62092d6f51de6b768f02;
Webots digest remains f0023e30daf38b172e4e6ad24ed345909bcd9551df34d63d824e121a7cebf099.
Full original631-file audits remain unchanged, fault hooks used only for the
explicit fault run. Fault-induced late ACKs are retained separately in raw
latency-analysis.json and are not included in the seven normal-run statistics.
