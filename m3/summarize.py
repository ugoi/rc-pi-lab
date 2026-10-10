"""Summarize measured results without deleting or relabeling development failures."""

import json, statistics
from pathlib import Path

root = Path(__file__).resolve().parents[1]
e = root / "evidence/m3"
runs = []
epochs = set()
factors = []
for p in sorted(e.glob("test-*.json")):
    d = json.loads(p.read_text())
    r = {
        "file": p.name,
        **{
            k: v
            for k, v in d.items()
            if k not in ("history", "rows", "physics_during_kill")
        },
    }
    runs.append(r)
    if d.get("result") == "PASS":
        for row in d.get("history", d.get("rows", [])):
            s = row["state"]
            epochs.add(s["epoch"])
            t = s.get("telemetry", {})
            if t.get("sim_s", 0) > 5:
                factors.append(t["factor"])
acks = []
late = 0
for p in e.glob("bridge-*.jsonl"):
    for l in p.read_text().splitlines():
        try:
            r = json.loads(l)
        except ValueError:
            continue
        if r.get("epoch") not in epochs:
            continue
        if r["event"] == "ack_correlated":
            acks.append(r["latency_s"])
        if r["event"] == "stop" and r.get("reason") == "late_guest_ack":
            late += 1
latencies = []
seen = set()
for p in e.glob("physics-*.jsonl"):
    for line in p.read_text().splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        c = r.get("source") or {}
        stamp = c.get("browser_sent_unix_ms")
        key = (c.get("epoch"), c.get("ack_seq"))
        if stamp and r.get("unix_ms") and abs(r["drive"]) > 0.04 and key not in seen:
            delay = (r["unix_ms"] - stamp) / 1000
            if 0 <= delay < 5:
                latencies.append(delay)
                seen.add(key)


def stats(v):
    v = sorted(v)
    return (
        {
            "samples": len(v),
            "min": min(v),
            "median": statistics.median(v),
            "p95": v[min(len(v) - 1, int(len(v) * 0.95))],
            "max": max(v),
        }
        if v
        else None
    )


out = {
    "runs": runs,
    "guest_ack_rtt_s": stats(acks),
    "late_ack_stops_in_pass_epochs": late,
    "webots_simulation_factor": stats(factors),
    "browser_to_physics_s": stats(latencies),
    "latency_scope": "Browser Date.now dispatch to first moving Webots sample for guest/PWM ACK; browser and both containers share Agent Services wall clock. Includes HTTP, guest, original I2C, bridge, physics and log sampling. Not a remote-client clock or physical Pi measurement.",
}
(e / "summary.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
