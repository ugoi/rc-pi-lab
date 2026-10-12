"""Observe the real crashed guest's init staying idle; no recovery/priming commands."""

import json, os, time, urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[2]
evidence = root / "evidence/m3"
url = os.environ.get("M3_URL", "http://127.0.0.1:18090")
text = (evidence / "serial.log").read_text()
assert "M3_APP_EXIT code=77" in text and "M3_IDLE_INIT" in text
before = json.load(urllib.request.urlopen(url + "/state", timeout=3))
ack_seq = before["ack"]["seq"]
pwm_seq = before["pwm"]["seq"]
start = time.monotonic()
rows = []
while time.monotonic() - start < 60:
    s = json.load(urllib.request.urlopen(url + "/state", timeout=3))
    rows.append({"wall": time.monotonic(), "state": s})
    assert s["mode"] == "STOPPED" and s["readiness"] == "unresponsive"
    assert s["ack"]["seq"] == ack_seq and s["pwm"]["seq"] == pwm_seq
    assert s["telemetry"]["drive"] == 0 and s["telemetry"]["speed_m_s"] < 0.03
    time.sleep(0.5)
later = (evidence / "serial.log").read_text()[len(text) :]
assert not any(line.startswith("M3 ") for line in later.splitlines()), (
    "guest application emitted new output after crash"
)
out = {
    "result": "PASS",
    "wall_s": time.monotonic() - start,
    "init": "M3_IDLE_INIT after exit 77",
    "rows": rows,
}
(evidence / ("idle-after-crash-" + str(time.time_ns()) + ".json")).write_text(
    json.dumps(out)
)
print("DURABLE_IDLE_PASS", out["wall_s"], flush=True)
