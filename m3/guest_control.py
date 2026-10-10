"""Same application bytes for Pi/Linux serial input; original Adafruit only.
The host watchdog is simulation-only. A real car requires a separate hardware cutoff.
"""

import json, math, os, select, signal, sys, time, tty

from adafruit_servokit import ServoKit

kit = ServoKit(channels=16, frequency=50)
for i in (0, 1):
    kit.servo[i].set_pulse_width_range(1000, 2000)


def write(steer, throttle):
    kit.servo[0].angle = 90 + 90 * steer
    kit.servo[1].angle = 90 + 90 * throttle


write(0, 0)
if sys.stdin.isatty():
    tty.setraw(sys.stdin.fileno())
input_fd = sys.stdin.fileno()

epoch = None
seq = -1
armed = False
last = time.monotonic()
previous = (0, 0)
print(
    "M3 "
    + json.dumps(
        {
            "event": "ready",
            "pid": os.getpid(),
            "stdin": os.readlink("/proc/self/fd/" + str(input_fd)),
            "guest_ns": time.monotonic_ns(),
        }
    ),
    flush=True,
)
buf = b""
while True:
    if time.monotonic() - last > 0.6 and armed:
        write(0, 0)
        armed = False
        previous = (0, 0)
        print(
            "M3 "
            + json.dumps(
                {
                    "event": "timeout",
                    "epoch": epoch,
                    "seq": seq,
                    "guest_ns": time.monotonic_ns(),
                }
            ),
            flush=True,
        )
    if not select.select([input_fd], [], [], 0.05)[0]:
        continue
    part = os.read(input_fd, 1024)
    if not part:
        write(0, 0)
        break
    buf += part
    if len(buf) > 4096:
        buf = b""
        write(0, 0)
        armed = False
        continue
    while b"\n" in buf:
        line, buf = buf.split(b"\n", 1)
        try:
            c = json.loads(line)
            print(
                "M3 "
                + json.dumps(
                    {"event": "received", "command": c, "guest_ns": time.monotonic_ns()}
                ),
                flush=True,
            )
            if c["op"] == "hello":
                if not isinstance(c["epoch"], str) or len(c["epoch"]) != 32:
                    raise ValueError()
                epoch = c["epoch"]
                seq = -1
                armed = False
                previous = (0, 0)
                write(0, 0)
            if c["epoch"] != epoch or type(c["seq"]) is not int or c["seq"] <= seq:
                raise ValueError()
            seq = c["seq"]
            last = time.monotonic()
            op = c["op"]
            s = c.get("steer", 0)
            t = c.get("throttle", 0)
            if any(type(v) not in (int, float) or not math.isfinite(v) for v in (s, t)):
                raise ValueError()
            s = max(-1, min(1, s))
            t = max(-1, min(1, t))
            if op == "arm":
                armed = True
                s = t = 0
            elif op in ("stop", "hello"):
                armed = False
                s = t = 0
            elif op == "drive":
                if not armed:
                    s = t = 0
            elif op == "test_freeze" and os.environ.get("M3_TESTING") == "1":
                os.kill(os.getpid(), signal.SIGSTOP)
            elif op == "test_crash" and os.environ.get("M3_TESTING") == "1":
                os._exit(77)
            else:
                raise ValueError()
            if (s, t) != previous:
                write(s, t)
                previous = (s, t)
            print(
                "M3 "
                + json.dumps(
                    {
                        "event": "ack",
                        "epoch": epoch,
                        "seq": seq,
                        "op": op,
                        "steer": s,
                        "throttle": t,
                        "armed": armed,
                        "guest_ns": time.monotonic_ns(),
                    }
                ),
                flush=True,
            )
        except (ValueError, KeyError, TypeError):
            write(0, 0)
            armed = False
            previous = (0, 0)
