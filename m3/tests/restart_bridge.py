import os

"""Bounded failure injection into the task container only; preserves guest and world."""

import json, subprocess, time, urllib.request, uuid
from pathlib import Path

URL = os.environ.get("M3_URL", "http://127.0.0.1:18090")
client = "restart-" + uuid.uuid4().hex
seq = 0
rows = []


def state():
    d = json.load(urllib.request.urlopen(URL + "/state", timeout=2))
    rows.append({"wall": time.monotonic(), "state": d})
    return d


epoch = state()["epoch"]


def command(op, throttle=0, epoch_override=None):
    global seq
    seq += 1
    data = {
        "epoch": epoch_override or epoch,
        "client": client,
        "seq": seq,
        "op": op,
        "steer": 0,
        "throttle": throttle,
        "ticket": state()["ticket"],
    }
    req = urllib.request.Request(
        URL + "/command",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json", "Origin": URL},
    )
    return urllib.request.urlopen(req, timeout=2).status


def drive(seconds, throttle):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        command("drive", throttle)
        time.sleep(0.15)


command("stop")
time.sleep(0.2)
command("arm")
drive(1.2, 0)
drive(1, 0.6)
assert state()["telemetry"]["speed_m_s"] > 0.1
script = 'import os,signal; [(os.kill(int(p),signal.SIGKILL)) for p in os.listdir("/proc") if p.isdigit() and int(p)!=os.getpid() and open("/proc/"+p+"/comm").read().strip()=="python3" and b"m3/bridge.py" in open("/proc/"+p+"/cmdline","rb").read()]'
start = time.monotonic()
subprocess.run(
    [
        "docker",
        "exec",
        "--user",
        "1001:1001",
        os.environ.get("M3_GUEST_CONTAINER", "rc-pi-m3-qemu"),
        "python3",
        "-c",
        script,
    ],
    check=True,
)
run = Path(__file__).resolve().parents[2] / "build/m3"
observations = []
while time.monotonic() - start < 2.5:
    t = json.loads((run / "telemetry.json").read_text())
    observations.append(t)
    if t["drive"] == 0 and t["speed_m_s"] < 0.03:
        break
    time.sleep(0.03)
else:
    raise AssertionError("bridge kill stop deadline")
stop_s = time.monotonic() - start
subprocess.run(
    [
        "docker",
        "exec",
        "-d",
        "--user",
        "1001:1001",
        "-e",
        "M3_TESTING=1",
        os.environ.get("M3_GUEST_CONTAINER", "rc-pi-m3-qemu"),
        "sh",
        "-c",
        "python3 m3/bridge.py >> evidence/m3/bridge-console.log 2>&1",
    ],
    check=True,
)
end = time.monotonic() + 5
while True:
    try:
        d = state()
        break
    except Exception:
        if time.monotonic() > end:
            raise
        time.sleep(0.1)
assert d["epoch"] != epoch and d["mode"] == "STOPPED"
try:
    command("arm")
    raise AssertionError("old epoch accepted")
except urllib.error.HTTPError as e:
    assert e.code == 409
new_epoch = d["epoch"]
epoch = new_epoch
drive(1.2, 0.6)
d = state()
assert d["mode"] == "STOPPED" and d["telemetry"]["speed_m_s"] < 0.03
out = (
    Path(__file__).resolve().parents[2]
    / "evidence/m3"
    / ("test-bridge-restart-" + str(time.time_ns()) + ".json")
)
out.write_text(
    json.dumps(
        {
            "result": "PASS",
            "stop_s": stop_s,
            "rows": rows,
            "physics_during_kill": observations,
        },
        indent=2,
    )
)
print(out, stop_s)
