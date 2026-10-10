"""Restart the owned guest/bridge Compose container; preserve its last PCA trace.

Stopping QEMU ends the container's supervisor as well. Therefore restart the
container, retain its configured fault/audit gates, and expect a new bridge epoch.
"""

import json, os, shutil, subprocess, time, urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[2]
container = os.environ.get("M3_GUEST_CONTAINER", "rc-pi-m3-qemu")
url = os.environ.get("M3_URL", "http://127.0.0.1:18090")
before = json.load(urllib.request.urlopen(url + "/state", timeout=3))
subprocess.run(["docker", "stop", "-t", "10", container], check=True)
label = str(time.time_ns())
shutil.copyfile(
    root / "evidence/m3/pca.jsonl",
    root / "evidence/m3" / ("pca-before-reboot-" + label + ".jsonl"),
)
start = time.monotonic()
subprocess.run(["docker", "start", container], check=True)
while time.monotonic() - start < 600:
    try:
        d = json.load(urllib.request.urlopen(url + "/state", timeout=3))
        if (
            d["epoch"] != before["epoch"]
            and d["ack"]
            and d["guest_age_s"] < 0.5
            and d["mode"] == "STOPPED"
        ):
            break
    except (OSError, ValueError):
        pass
    time.sleep(0.5)
else:
    raise SystemExit("Guest/bridge restart deadline")
result = {
    "result": "READY_STOPPED",
    "wall_s": time.monotonic() - start,
    "scope": "guest and bridge container restarted; existing configured fault/audit flags retained",
    "previous_epoch": before["epoch"],
    "state": d,
}
(root / "evidence/m3" / ("guest-reboot-" + label + ".json")).write_text(
    json.dumps(result, indent=2)
)
print("GUEST_RESTART_READY", result["wall_s"], flush=True)
