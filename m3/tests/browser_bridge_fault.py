"""Real browser input and bridge death, observed independently in physics telemetry.
Starts a disposable browser process; never controls the personal browser.
"""

import json, os, subprocess, time, urllib.request
from pathlib import Path
from browser_client import browser_command, close as close_browser

root = Path(__file__).resolve().parents[2]
evidence = root / "evidence/m3"
url = os.environ.get("M3_URL", "http://127.0.0.1:18090")
container = os.environ.get("M3_GUEST_CONTAINER", "rc-pi-m3-qemu")
session = os.environ.get("M3_BROWSER_SESSION", "ste112")
label = str(time.time_ns())
rows = []
result = {
    "result": "FAIL",
    "case": "browser_bridge_kill",
    "client": "Isolated headless Chromium process via private CDP pipes, real Input events",
}


def browser(*args):
    d = browser_command(args)
    with (evidence / ("browser-client-" + label + ".jsonl")).open("a") as f:
        f.write(json.dumps(dict(args=args, response=d)) + "\n")
    assert d.get("success"), d
    return d["data"]


def state():
    return json.load(urllib.request.urlopen(url + "/state", timeout=2))


recording = False
try:
    assert state()["readiness"] == "ready"
    result["browser"] = browser("tab", "__owned__")
    browser("open", url)
    browser("set", "viewport", "1280", "900")
    browser(
        "record",
        "start",
        str(evidence / ("browser-bridge-fault-" + label + ".mp4")),
        "--fps",
        "15",
    )
    recording = True
    browser("click", "#arm")
    end = time.monotonic() + 4
    while state()["mode"] != "ARMED":
        assert time.monotonic() < end, "arming deadline"
        time.sleep(0.1)
    browser("focus", "#throttle")
    browser("press", "End")
    end = time.monotonic() + 3
    while True:
        before = state()
        if before["telemetry"]["speed_m_s"] > 0.54:
            break
        assert time.monotonic() < end, "no browser-driven motion"
        time.sleep(0.1)
    result["before"] = before
    kill = 'import os,signal; [(os.kill(int(p),signal.SIGKILL)) for p in os.listdir("/proc") if p.isdigit() and int(p)!=os.getpid() and open("/proc/"+p+"/comm").read().strip()=="python3" and b"m3/bridge.py" in open("/proc/"+p+"/cmdline","rb").read()]'
    start = time.monotonic()
    subprocess.run(["docker", "exec", container, "python3", "-c", kill], check=True)
    while time.monotonic() - start < 2.5:
        t = json.loads((root / "build/m3/telemetry.json").read_text())
        rows.append(t)
        if t["drive"] == 0 and t["speed_m_s"] < 0.03:
            break
        time.sleep(0.02)
    else:
        raise AssertionError("bridge stop deadline")
    result["stop_s"] = time.monotonic() - start
    assert (t["mode"], t["reason"], t["source_status"]) == (
        "STOPPED",
        "bridge_timeout",
        "stale",
    ), t
    assert t["source"]["mode"] == "ARMED"
    result["ui_disconnected"] = browser("get", "text", "#status")["text"]
    assert result["ui_disconnected"] == "VERBINDUNG UNTERBROCHEN"
    result["ui_feed"] = browser("get", "text", "#feed")["text"]
    assert result["ui_feed"] == "LETZTER STAND"
    assert "veraltet" in browser("get", "text", "#metrics")["text"]
    browser(
        "screenshot", str(evidence / ("browser-bridge-disconnected-" + label + ".png"))
    )
    subprocess.run(
        [
            "docker",
            "exec",
            "-d",
            container,
            "sh",
            "-c",
            "python3 m3/bridge.py >> evidence/m3/bridge-console.log 2>&1",
        ],
        check=True,
    )
    end = time.monotonic() + 10
    while True:
        try:
            after = state()
            if after["readiness"] == "ready" and after["guest_age_s"] < 0.5:
                break
        except (OSError, ValueError):
            pass
        assert time.monotonic() < end, "bridge restart readiness deadline"
        time.sleep(0.1)
    time.sleep(0.5)
    after = state()
    result["after"] = after
    assert after["epoch"] != before["epoch"] and after["mode"] == "STOPPED"
    assert after["telemetry"]["speed_m_s"] < 0.03
    assert browser("get", "value", "#throttle")["value"] == "0"
    result["ui_reconnected"] = browser("get", "text", "#status")["text"]
    assert result["ui_reconnected"] == "GESTOPPT"
    browser(
        "screenshot", str(evidence / ("browser-bridge-reconnected-" + label + ".png"))
    )
    result["result"] = "PASS"
except Exception as error:
    result["error"] = repr(error)
    raise
finally:
    recording_failure = None
    if recording:
        try:
            browser("record", "stop")
        except Exception as error:
            result["recording_error"] = repr(error)
            if result["result"] == "PASS":
                result["result"] = "FAIL"
                recording_failure = error
    try:
        close_browser()
    except Exception as error:
        result["cleanup_error"] = repr(error)
        result["result"] = "FAIL"
        recording_failure = error
    result["physics_during_kill"] = rows
    (evidence / ("browser-bridge-fault-" + label + ".json")).write_text(
        json.dumps(result, indent=2)
    )
    print(
        {
            k: v
            for k, v in result.items()
            if k not in ["before", "after", "physics_during_kill"]
        },
        flush=True,
    )

    if recording_failure is not None:
        raise RuntimeError("browser video or cleanup failed; evidence saved") from recording_failure
