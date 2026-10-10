# QA corrections, 2026-10-10

This supersedes the reproduction/observer claims affected by F1–F3 in the first
acceptance report. Historical evidence and the delivered SD image are preserved.
It does not extend acceptance to real hardware or the full RC vehicle.

## F1: decompression memory

The pinned XZ 5.8.1 defaults to automatic threading based on host cores. QA saw an
OOM kill at the documented 2-GiB cgroup limit. `extract-image.sh` now explicitly
passes `--threads=1 --memlimit-decompress=256MiB`, overriding threading defaults
and leaving room for tools and reclaimable page cache. Failure removes its partial
image; successful decompression is atomically renamed as before. Validation uses
the original script invocation, no environment override, and records cgroup
limits, memory events before/after, peak memory and exit status.

## F2: launch readiness and phase deadlines

In QA's failing trace the second command was echoed, then no new I2C transaction
or `ANGLE 0` appeared before the old ten-second socket timeout. This localises the
observed failure before first PWM; it does not establish why Python startup was
slower in that run. QA's later 6.93-second run is not a causal reproduction.

The harness now separates shell dispatch, original-app readiness, first PWM,
reconnect and completion. Continuous readers prevent the serial and PWM streams
from blocking each other's observation. A fresh connection's sequence establishes
the lower bound for second-run events. Exact serial-line matching cannot accept
echoed commands as success. Finite phase and total deadlines fail visibly and save
a FAIL result with the last observation. No guest app/library/model changes are
required. All diagnostic boots use temporary snapshots of the same prepared
rootfs, so each run begins with identical persistent guest state.

The 60-second startup budget is a bounded TCG test allowance, not a measured
hardware latency guarantee. Three complete runs and a deliberately absent
readiness marker test its behaviour; the original intermittent latency cause
remains unisolated unless separate evidence proves it.

## F3: observer protocol validation

`pwm_protocol.py` validates the actual device schema, types and bounds before an
observation is emitted. Invalid complete frames produce `framing_error` with
`valid:false`, and consumption resumes at the next newline. Missing delimiters
are bounded at 4096 bytes; EOF with a partial frame is invalid. Every termination
invalidates the state. Reconnection is an explicit fresh consumer invocation.
The QA helper's case named `valid` supplies only `high_us`; this is not a complete
device frame and is now correctly rejected. Original complete device samples
remain accepted. This is an observer contract, not a physical motor stop guarantee.

## Validation scope

Host protocol/process tests and the missing-readiness negative case are distinct
from three actual Pi-OS diagnostic runs, each with two original-app executions,
package integrity checks, register matrix and reconnect. The model C code, guest
files, wheel pins, kernel and DTB are unchanged. Consequently no new full-systemd
image build or upload is required; the existing two independent QA systemd boots
and delivered image remain the historical evidence for those unchanged layers.
The new raw test results and exact source revision are delivered in an additional
manifested evidence archive. Independent recheck remains with existing STE-92.

## Observed correction results

CTO execution in the documented 4-CPU/2-GiB/no-extra-swap container passed.
Independent recheck of this revision remains pending in STE-92.

| Run | Cold boot to first app complete (s) | Repeat ready (s) | Repeat first PWM (s) | Result |
|---|---:|---:|---:|---|
| 1 | 235.07 | 9.644 | 9.657 | PASS |
| 2 | 243.11 | 7.380 | 7.385 | PASS |
| 3 | 242.47 | 9.094 | 9.108 | PASS |

Each run passed both app executions, the 631-file original-package audit, the
register matrix, reconnect, full-off and clean remount. The base rootfs SHA
remained identical after every run. Extraction exited 0 with zero OOM/OOM-kill
events before and after; total cgroup peak including page cache reached 2 GiB.
Eight host regression tests passed, the unchanged QA fault helper had no crashes
or accepted invalid PWM, all 408 historical original trace frames decoded, and
two real QEMU observer restarts produced fresh snapshots (seq 8 and 10).

Machine-readable results: `evidence/qa-fixes-20261010.json`. Full per-run logs,
raw traces, counters and the tested source hashes are in the supplemental archive.
