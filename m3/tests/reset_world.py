import os

"""Explicit scenario reset by restarting the owned physics process, never driving a pose."""

import json, subprocess, time
from pathlib import Path

root = Path(__file__).resolve().parents[2]
start = time.monotonic()
subprocess.run(
    [
        "docker",
        "restart",
        "-t",
        "1",
        os.environ.get("M3_PHYSICS_CONTAINER", "rc-pi-m3-webots"),
    ],
    check=True,
)
while time.monotonic() - start < 90:
    try:
        d = json.loads((root / "build/m3/telemetry.json").read_text())
        if (
            d["wall"] > start
            and d["sim_s"] < 40
            and abs(d["position"][0]) < 0.01
            and abs(d["position"][1]) < 0.01
        ):
            print("WORLD_RESET_READY", time.monotonic() - start)
            break
    except (OSError, ValueError, KeyError):
        pass
    time.sleep(0.2)
else:
    raise SystemExit("World reset deadline")
(root / "evidence/m3" / ("world-reset-" + str(time.time_ns()) + ".json")).write_text(
    json.dumps(
        {"start_wall": start, "ready_wall": time.monotonic(), "first_state": d},
        indent=2,
    )
)
