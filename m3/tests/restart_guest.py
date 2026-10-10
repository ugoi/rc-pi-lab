"""Restart the owned disposable guest snapshot; retain the stopped raw trace."""

import json, os, shutil, subprocess, time, urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[2]
container = os.environ.get("M3_GUEST_CONTAINER", "rc-pi-m3-qemu")
url = os.environ.get("M3_URL", "http://127.0.0.1:18090")
before = json.load(urllib.request.urlopen(url + "/state", timeout=3))
oldseq = (before["ack"] or {}).get("seq", -1)
script = """import os,signal,time
from pathlib import Path
def qemus():
 result=[]
 for p in Path('/proc').glob('[0-9]*/comm'):
  try:
   if p.read_text().strip().startswith('qemu-system'): result.append(int(p.parent.name))
  except FileNotFoundError:pass
 return result
for pid in qemus():os.kill(pid,signal.SIGTERM)
end=time.monotonic()+10
while qemus() and time.monotonic()<end:time.sleep(.1)
assert not qemus(), 'QEMU did not stop'
"""
subprocess.run(
    ["docker", "exec", "--user", "1001:1001", container, "python3", "-c", script],
    check=True,
)
label = str(time.time_ns())
shutil.copyfile(
    root / "evidence/m3/pca.jsonl",
    root / "evidence/m3" / ("pca-before-reboot-" + label + ".jsonl"),
)
start = time.monotonic()
subprocess.run(
    [
        "docker",
        "exec",
        "-d",
        "--user",
        "1001:1001",
        "-e",
        "M3_TESTING=1",
        "-e",
        "M3_REUSE_AUDIT=1",
        container,
        "sh",
        "-c",
        "sh m3/boot.sh >> evidence/m3/qemu.log 2>&1",
    ],
    check=True,
)
while time.monotonic() - start < 600:
    try:
        d = json.load(urllib.request.urlopen(url + "/state", timeout=3))
        if (
            d["ack"]
            and d["ack"]["seq"] > oldseq
            and d["guest_age_s"] < 0.5
            and d["mode"] == "STOPPED"
        ):
            break
    except (OSError, ValueError):
        pass
    time.sleep(0.5)
else:
    raise SystemExit("Guest restart deadline")
result = {
    "result": "READY_STOPPED",
    "wall_s": time.monotonic() - start,
    "audit": "reused from unchanged derived image",
    "state": d,
}
(root / "evidence/m3" / ("guest-reboot-" + label + ".json")).write_text(
    json.dumps(result, indent=2)
)
print("GUEST_RESTART_READY", result["wall_s"], flush=True)
