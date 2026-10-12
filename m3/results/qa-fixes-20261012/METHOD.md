# F1/F2 correction acceptance — 2026-10-12

Before corrected acceptance: retain 600 wall seconds for each full guest start;
maximum-throttle fault stops must reach <0.03 m/s within 2.5 wall seconds. All
attempts, including failures, are recorded. No manual serial priming or loop of
restarts until PASS. Original M1/M2 guest packages, QEMU device binary, DTB and
kernel remain unchanged. Separate Compose projects/ports/container names isolate
this task from QA and the stopped historical review runtime.

Sequence:
1. Unmodified 387711d normal start, one attempt, full 631-file audit, observe 600 s.
2. Unmodified guest/bridge with QEMU UART trace only, one diagnostic start, 600 s.
3. Corrected guest/bridge/Webots normal configuration M3_TESTING=0; full audit,
   first start with neutral fresh ACK, actual German browser startup screen.
4. Actual browser arm/gas, bridge SIGKILL, independent physics mode/reason/stop
   deadline, browser connection-loss display, new bridge epoch and explicit rearm.
5. Corrected fault configuration M3_TESTING=1, full audit. Full-throttle SIGSTOP,
   full guest/bridge restart using the checked-in helper, fresh neutral ACK.
6. Full-throttle guest crash (exit 77), init idle and 60 s durable idle with held
   PWM and stopped physics, then full guest/bridge restart with fresh neutral ACK.
7. Final normal configuration M3_TESTING=0, full audit and neutral readiness on
   the delivered source. Targeted motion/replay/heartbeat and source regressions.

Source diagnosis references (context, not substitutes for local trace evidence):
- QEMU v10.1.0 PL011: https://github.com/qemu/qemu/blob/v10.1.0/hw/char/pl011.c
- Pi Linux PL011: https://github.com/raspberrypi/linux/blob/rpi-6.12.y/drivers/tty/serial/amba-pl011.c
  (`pl011_enable_interrupts`, bounded 2*fifosize drain; branch read 2026-10-12,
  not a claim that this moving branch is the exact kernel build source).

The trace test retains source/binary pins and changes only QEMU's built-in trace
flags. The UART RX FIFO is filled by host hello bytes during boot. Linux clears
RX status and drains 32 bytes; QEMU replenishes from the queued host bytes while
this happens. The trace then ends with RX FIFO 16/16 and can_receive=0, without
further reads, through app ready and all three later hello attempts. This is the
first failing boundary. QEMU asserts RX only at the threshold crossing (one byte),
and its RX-enable bits do not gate input. The bounded Linux drain therefore does
not reliably clear a queued pre-boot stream. The application fix sends nothing
until the raw UART is configured and neutral PWM written; idle readiness beacons
let a replacement bridge discover the already-running guest. The QEMU/kernel
model is not patched. The separate direct-send/timer Hello-spacing race is also
fixed centrally and regression-tested.

These are simulation checks. Existing independent QA PASS cases remain historical;
STE-114 independently checks this new commit. No Mac/Safari, remote personal
client, real Pi boot, electrical or hardware cutoff acceptance is implied.

The 49 RX bytes in the complete failed trace exactly match the prefix of the first 172-byte pre-boot hello. No later hello reaches RX. Thus the initial stall predates the post-ready reader/timer burst; that burst is a separate scheduling defect, not the demonstrated cause of this stall.
