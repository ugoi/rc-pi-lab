"""Real browser drive + simulated guest scheduling stall; no fault hooks required.

Pauses only QEMU in the explicitly named guest container. The bridge and physics
continue. Late ACKs must not restore drive, and the page must clear its sliders.
"""
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path
from browser_client import browser_command

root = Path(__file__).resolve().parents[2]
evidence = root / "evidence/m3"
url = os.environ.get("M3_URL", "http://127.0.0.1:18090")
container = os.environ.get("M3_GUEST_CONTAINER", "rc-pi-m3-qemu")
session = os.environ.get("M3_BROWSER_SESSION", "ste112")
label = str(time.time_ns())
result = {"result": "FAIL", "case": "browser_guest_pause", "samples": []}


def browser(*args):
    data = browser_command(args)
    with (evidence / ("browser-client-" + label + ".jsonl")).open("a") as f:
        f.write(json.dumps(dict(args=args, response=data)) + "\n")
    assert data.get("success"), data
    return data["data"]


def state():
    return json.load(urllib.request.urlopen(url + "/state", timeout=2))


def signal_qemu(sig):
    code = """import os,signal,sys
pids=[int(p) for p in os.listdir('/proc') if p.isdigit() and
      open('/proc/'+p+'/comm').read().strip().startswith('qemu-system-')]
assert len(pids)==1,pids
os.kill(pids[0],getattr(signal,sys.argv[1]))
print(pids[0])
"""
    r = subprocess.run(["docker", "exec", container, "python3", "-c", code, sig],
                       capture_output=True, text=True, timeout=5, check=True)
    return int(r.stdout.strip())


paused = recording = False
try:
    assert state()["readiness"] == "ready"
    browser("tab", os.environ.get("M3_BROWSER_TARGET", "__owned__"))
    browser("open", url)
    browser("record", "start", str(evidence / ("browser-pause-" + label + ".mp4")), "--fps", "15")
    recording = True
    browser("click", "#arm")
    end = time.monotonic() + 4
    while state()["mode"] != "ARMED":
        assert time.monotonic() < end, "arming deadline"
        time.sleep(.1)
    browser("focus", "#throttle")
    browser("press", "End")
    end = time.monotonic() + 3
    while True:
        before = state()
        if before["telemetry"]["speed_m_s"] > .54:
            break
        assert time.monotonic() < end, "no browser-driven motion"
        time.sleep(.1)
    result["before"] = before
    start = time.monotonic()
    result["pause_started_wall_ns"] = int(start * 1e9)
    result["qemu_pid"] = signal_qemu("SIGSTOP")
    paused = True
    while time.monotonic() - start < 2.5:
        s = state()
        result["samples"].append({"elapsed_s": time.monotonic() - start, "state": s})
        if s["telemetry"]["speed_m_s"] < .03 and s["telemetry"]["drive"] == 0:
            break
        time.sleep(.02)
    else:
        raise AssertionError("guest stall stop deadline")
    result["stop_s"] = time.monotonic() - start
    assert s["mode"] == "STOPPED" and s["reason"] == "guest_liveness_timeout", s
    # Keep the guest paused long enough to make queued ACKs stale on recovery.
    time.sleep(max(0, 1.5 - (time.monotonic() - start)))
    signal_qemu("SIGCONT")
    result["pause_resumed_wall_ns"] = time.monotonic_ns()
    paused = False
    end = time.monotonic() + 10
    while True:
        after = state()
        assert after["mode"] == "STOPPED", "automatic rearm"
        assert after["telemetry"]["speed_m_s"] < .03, "automatic motion"
        if after["readiness"] == "ready" and after["guest_age_s"] < .5:
            break
        assert time.monotonic() < end, "fresh neutral recovery deadline"
        time.sleep(.1)
    time.sleep(.5)
    result["after"] = state()
    result["ui_status"] = browser("get", "text", "#status")["text"]
    result["ui_reason"] = browser("get", "text", "#reason")["text"]
    assert result["ui_status"] == "SICHERHEITSSTOPP"
    assert browser("get", "value", "#throttle")["value"] == "0"
    assert not browser("is", "enabled", "#throttle")["enabled"]
    browser("screenshot", str(evidence / ("browser-pause-" + label + ".png")))
    result["result"] = "PASS"
except Exception as error:
    result["error"] = repr(error)
    raise
finally:
    recording_failure = None
    if paused:
        signal_qemu("SIGCONT")
    if recording:
        try:
            browser("record", "stop")
        except Exception as error:
            result["recording_error"] = repr(error)
            if result["result"] == "PASS":
                result["result"] = "FAIL"
                recording_failure = error
    (evidence / ("browser-pause-" + label + ".json")).write_text(json.dumps(result, indent=2))
    print({k: v for k, v in result.items() if k not in ("samples", "before", "after")}, flush=True)

    if recording_failure is not None:
        raise RuntimeError("video recording failed; control evidence saved") from recording_failure
