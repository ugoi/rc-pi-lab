#!/bin/sh
# Actual user-facing browser inputs, not a replay or direct actuator injection.
set -eu
cd "$(dirname "$0")/../.."
BROWSER_SESSION=${M3_BROWSER_SESSION:-ste112}
python3 - <<'PY'
import os, json, urllib.request
from pathlib import Path
s = json.load(urllib.request.urlopen(os.environ.get('M3_URL', 'http://127.0.0.1:18090') + '/state'))
assert s['telemetry_age_s'] < .5 and s['guest_age_s'] < .5, 'Wait for fresh guest and physics before recording'
assert s['mode'] == 'STOPPED', 'Stop before recording'
Path('evidence/m3/browser-before.json').write_text(json.dumps(s))
PY
agent-browser --session "$BROWSER_SESSION" open "${M3_URL:-http://127.0.0.1:18090}"
agent-browser --session "$BROWSER_SESSION" record start "$PWD/evidence/m3/driving-live.mp4" --fps 15
trap 'agent-browser --session "$BROWSER_SESSION" click "#stop" >/dev/null 2>&1 || true; agent-browser --session "$BROWSER_SESSION" record stop' EXIT INT TERM
agent-browser --session "$BROWSER_SESSION" click '#arm'
sleep 2
agent-browser --session "$BROWSER_SESSION" get text '#status' > evidence/m3/browser-arm.json
cat evidence/m3/browser-arm.json
python3 -c 'import json; assert json.load(open("evidence/m3/browser-arm.json"))["data"]["text"] == "ARMED"'
agent-browser --session "$BROWSER_SESSION" focus '#throttle'
for i in 1 2 3 4 5 6; do agent-browser --session "$BROWSER_SESSION" press ArrowRight; done
sleep 2
agent-browser --session "$BROWSER_SESSION" focus '#steer'
for i in 1 2 3 4 5 6 7 8; do agent-browser --session "$BROWSER_SESSION" press ArrowRight; done
sleep 2
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16; do agent-browser --session "$BROWSER_SESSION" press ArrowLeft; done
sleep 2
agent-browser --session "$BROWSER_SESSION" click '#center'
agent-browser --session "$BROWSER_SESSION" click '#stop'
sleep 1
agent-browser --session "$BROWSER_SESSION" mouse move 500 300
agent-browser --session "$BROWSER_SESSION" mouse down
agent-browser --session "$BROWSER_SESSION" mouse move 620 340
agent-browser --session "$BROWSER_SESSION" mouse up
agent-browser --session "$BROWSER_SESSION" mouse wheel -180
agent-browser --session "$BROWSER_SESSION" screenshot "$PWD/evidence/m3/browser-driving.png"
agent-browser --session "$BROWSER_SESSION" get text '#metrics'
python3 - <<'PY'
import os, json, urllib.request, math
from pathlib import Path
s = json.load(urllib.request.urlopen(os.environ.get('M3_URL', 'http://127.0.0.1:18090') + '/state'))
b = json.loads(Path('evidence/m3/browser-before.json').read_text())
assert s['mode'] == 'STOPPED' and s['telemetry']['speed_m_s'] < .03
assert math.dist(s['telemetry']['position'], b['telemetry']['position']) > .05, 'No actual vehicle motion'
Path('evidence/m3/browser-after.json').write_text(json.dumps(s))
print('BROWSER_DRIVE_STOP_PASS')
PY
