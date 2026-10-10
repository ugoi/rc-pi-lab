import os

"""Real HTTP -> guest -> original I2C -> PWM -> Webots acceptance.
No fake data. Run when no human browser holds the lease; writes own JSON evidence.
Destructive-to-this-sim fault cases are explicit flags. Never changes source/world.
"""

import argparse, json, time, urllib.request, urllib.error, uuid
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument(
    "--case",
    choices=["motion", "obstacle", "disconnect", "freeze", "crash", "stale"],
    required=True,
)
parser.add_argument('--drive-throttle', type=float, default=0.6,
                    help='Throttle for disconnect/freeze/crash cases, within (0,1]')
a = parser.parse_args()
assert 0 < a.drive_throttle <= 1
url = os.environ.get("M3_URL", "http://127.0.0.1:18090")
seq = 0
client = "test-" + uuid.uuid4().hex
out = (
    Path(__file__).resolve().parents[2]
    / "evidence/m3"
    / ("test-" + a.case + "-" + str(time.time_ns()) + ".json")
)
history = []


def state():
    d = json.load(urllib.request.urlopen(url + "/state", timeout=3))
    history.append({"observed": time.monotonic(), "state": d})
    return d


epoch = state()["epoch"]


def command(op="drive", steer=0, throttle=0, **override):
    global seq
    seq += 1
    c = dict(
        ticket=state()["ticket"],
        epoch=epoch,
        client=client,
        seq=seq,
        op=op,
        steer=steer,
        throttle=throttle,
    )
    c.update(override)
    req = urllib.request.Request(
        url + "/command",
        data=json.dumps(c).encode(),
        headers={"Content-Type": "application/json", "Origin": url},
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.load(e)


def drive(seconds, steer=0, throttle=0):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        code, res = command(steer=steer, throttle=throttle)
        assert code == 200, res
        time.sleep(0.15)
        d = state()
    return d


def arm():
    code, res = command("arm")
    assert code == 200, res
    d = drive(1.2)
    assert d["mode"] == "ARMED", (d["mode"], d["reason"])


def stopped(start, reason=None):
    while time.monotonic() - start < 2.5:
        d = state()
        if d["mode"] == "STOPPED" and d["telemetry"]["speed_m_s"] < 0.03:
            if reason:
                assert reason in d["reason"], d["reason"]
            return time.monotonic() - start
        time.sleep(0.05)
    raise AssertionError("stop deadline missed")


result = {"case": a.case, "start": time.monotonic(), "fault_drive_throttle": a.drive_throttle}
try:
    command("stop")
    time.sleep(0.3)
    arm()
    if a.case == "motion":
        origin = state()["telemetry"]["position"]
        d = drive(1.5, throttle=0.6)
        assert d["telemetry"]["position"][0] > origin[0] + 0.15
        d = drive(1.3, steer=0.65, throttle=0.4)
        assert d["telemetry"]["steering"][0] > 0.2
        d = drive(1.3, steer=-0.65, throttle=0.4)
        assert d["telemetry"]["steering"][0] < -0.2
        d = drive(0.8, steer=2, throttle=0)
        assert d["ack"]["steer"] == 1, "Steering saturation failed"
        d = drive(1.5, throttle=-0.4)
        t = d["telemetry"]
        forward = [t["orientation"][i] for i in (0, 3, 6)]
        assert sum(x * y for x, y in zip(t["velocity"][:3], forward)) < -0.05, (
            "Reverse not observed"
        )
        start = time.monotonic()
        command("stop")
        result["stop_s"] = stopped(start)
    elif a.case == "obstacle":
        initial = state()["telemetry"]["position"]
        assert abs(initial[0]) < 0.01 and abs(initial[1]) < 0.01, (
            "Restart world before obstacle case"
        )
        d = drive(8, throttle=0.7)
        t = d["telemetry"]
        assert 1.2 < t["position"][0] < 1.7, t["position"]
        assert any(
            pt[2] > 0.02 and 1.60 < pt[0] < 1.70
            for row in history
            for pt in row["state"]["telemetry"].get("contacts", [])
        ), "No obstacle contact"
        assert t["speed_m_s"] < 0.08, t["speed_m_s"]
        result["collision_position"] = t["position"]
        start = time.monotonic()
        command("stop")
        result["stop_s"] = stopped(start)
    elif a.case == "disconnect":
        d = drive(2, throttle=a.drive_throttle)
        result['speed_before_fault_m_s'] = d['telemetry']['speed_m_s']
        assert d["telemetry"]["speed_m_s"] > 0.1
        start = time.monotonic()
        result["stop_s"] = stopped(start, "browser_timeout")
        d = drive(0.5, throttle=0.6)
        assert d["mode"] == "STOPPED"
    elif a.case in ("freeze", "crash"):
        d = drive(2, throttle=a.drive_throttle)
        result['speed_before_fault_m_s'] = d['telemetry']['speed_m_s']
        assert d["telemetry"]["speed_m_s"] > 0.1
        before = d["pwm"]["high_us"][1]
        start = time.monotonic()
        command("test_" + a.case)
        d = drive(1.1, throttle=0.6)
        result["stop_s"] = stopped(start, "guest_liveness")
        assert abs(state()["pwm"]["high_us"][1] - before) < 0.01, (
            "PCA did not hold commanded pulse"
        )
        result["held_pwm_us"] = before
    elif a.case == "stale":
        d = drive(0.5, throttle=0.5)
        command("stop")
        time.sleep(0.2)
        assert command("drive", throttle=1, seq=1)[0] == 409
        assert command("arm", epoch="0" * 32)[0] == 409
        old_ticket = state()["ticket"]
        time.sleep(0.9)
        assert command("arm", ticket=old_ticket)[0] == 409
        d = drive(0.5, throttle=0.5)
        assert d["mode"] == "STOPPED"
    result["result"] = "PASS"
except Exception as e:
    result["result"] = "FAIL"
    result["error"] = repr(e)
    raise
finally:
    result["history"] = history
    out.write_text(json.dumps(result, indent=2))
    print(out)
    print({k: v for k, v in result.items() if k != "history"})
