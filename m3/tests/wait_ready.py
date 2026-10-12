"""One bounded startup observation. Never primes serial or restarts anything."""

import json, os, time, urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[2]
url = os.environ.get("M3_URL", "http://127.0.0.1:18090")
label = os.environ.get("M3_ATTEMPT", str(time.time_ns()))
start = time.monotonic()
rows = []
result = {"attempt": label, "deadline_s": 600, "result": "FAIL"}
try:
    while time.monotonic() - start < 600:
        try:
            s = json.load(urllib.request.urlopen(url + "/state", timeout=3))
            rows.append({"wall": time.monotonic(), "state": s})
            elapsed = s.get("startup_elapsed_s", time.monotonic() - start)
            if elapsed > 600:
                break
            if (
                s.get("readiness") == "ready"
                and s["guest_age_s"] < 0.5
                and s["telemetry_age_s"] < 0.5
                and s["mode"] == "STOPPED"
                and s["ack"]["steer"] == s["ack"]["throttle"] == 0
                and all(abs(v - 1500) < 10 for v in s["pwm"]["high_us"][:2])
            ):
                result.update(result="PASS", wall_s=elapsed, epoch=s["epoch"])
                break
        except (OSError, ValueError) as e:
            rows.append({"wall": time.monotonic(), "error": str(e)})
        time.sleep(0.5)
    assert result["result"] == "PASS", "Readiness deadline (600 s)"
finally:
    result["observations"] = rows
    (root / "evidence/m3" / ("readiness-" + label + ".json")).write_text(
        json.dumps(result)
    )
    print({k: v for k, v in result.items() if k != "observations"}, flush=True)
