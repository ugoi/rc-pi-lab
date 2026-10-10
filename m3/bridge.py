"""Browser -> serial guest. Actuator output only from validated QEMU PWM.
Monotonic wall-clock watchdogs gate physics independently of held PCA registers.
"""

import json, math, os, socket, sys, threading, time, uuid
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from pwm_protocol import decode_frame

ROOT = Path(__file__).resolve().parents[1]
RUN = Path(os.environ.get("M3_RUN_DIR", str(ROOT / "build/m3")))
EVID = Path(os.environ.get("M3_EVIDENCE_DIR", str(ROOT / "evidence/m3")))
P = json.loads((ROOT / "m3/parameters.json").read_text())
RUN.mkdir(exist_ok=True)
EVID.mkdir(exist_ok=True)
EPOCH = uuid.uuid4().hex
lock = threading.RLock()
loglock = threading.Lock()
logfile = (EVID / f"bridge-{EPOCH}.jsonl").open("w", buffering=1)


def log(event, **kw):
    with loglock:
        logfile.write(
            json.dumps(
                dict(event=event, wall_ns=time.monotonic_ns(), epoch=EPOCH, **kw),
                allow_nan=False,
            )
            + "\n"
        )


def atomic(path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, allow_nan=False))
    tmp.replace(path)


class State:
    def __init__(self):
        self.mode = "STOPPED"
        self.reason = "startup"
        self.client = None
        self.client_seq = -1
        self.client_sequences = {}
        self.tickets = {}
        self.browser = 0
        self.browser_sent_unix_ms = None
        self.guest = 0
        self.pwm = None
        self.pwm_seq = 0
        self.command_seq = 0
        self.ack = None
        self.pending = {}
        self.serial = None
        self.target = (0, 0)
        self.arm_at = 0
        self.last_tx = 0
        self.need_stop = False
        self.telemetry = {}
        self.connected = False
        self.ready = False
        self.hello_attempts = 0

    def stop(self, reason):
        if self.mode != "STOPPED" or self.reason != reason:
            log("stop", reason=reason)
        self.mode = "STOPPED"
        self.reason = reason
        self.target = (0, 0)
        self.need_stop = True

    def send(self, op, steer=0, throttle=0):
        if self.serial is None:
            return
        if op == "hello":
            self.hello_attempts += 1
        self.command_seq += 1
        c = dict(
            epoch=EPOCH,
            seq=self.command_seq,
            op=op,
            steer=steer,
            throttle=throttle,
            browser_seq=self.client_seq,
            browser_client=self.client,
            browser_sent_unix_ms=self.browser_sent_unix_ms,
        )
        self.pending[self.command_seq] = (time.monotonic(), c)
        self.pending = {
            k: v for k, v in self.pending.items() if time.monotonic() - v[0] < 2
        }
        try:
            raw = (("\n" if op == "hello" else "") + json.dumps(c) + "\n").encode()
            if self.serial.send(raw, socket.MSG_DONTWAIT) != len(raw):
                raise OSError("partial serial send")
            log("serial_tx", command=c)
        except OSError:
            self.serial = None
            self.stop("serial_disconnected")


S = State()


def pwm_reader():
    while True:
        try:
            sock = socket.socket(socket.AF_UNIX)
            sock.connect(str(RUN / "pwm.sock"))
            with lock:
                S.pwm_seq = 0
                S.pwm = None
                S.stop("pwm_connected_rearm_required")
            with sock, sock.makefile("rb") as f:
                while True:
                    line = f.readline(4098)
                    if not line:
                        raise OSError("EOF")
                    row = decode_frame(line)
                    with lock:
                        if row["seq"] <= S.pwm_seq:
                            raise ValueError("stale PWM")
                        S.pwm_seq = row["seq"]
                        if row["event"] in ("stop", "bridge_open"):
                            S.pwm = row
                            log("pwm", row=row)
        except (OSError, ValueError) as e:
            with lock:
                S.pwm = None
                S.stop("pwm_disconnected_or_invalid")
            log("pwm_error", error=str(e))
            time.sleep(0.5)


def serial_reader():
    while True:
        try:
            sock = socket.socket(socket.AF_UNIX)
            sock.settimeout(1)
            sock.connect(str(RUN / "serial.sock"))
            sock.settimeout(None)
            with lock:
                S.serial = sock
                S.ready = False
                S.hello_attempts = 0
                S.pending = {}
                S.stop("serial_connected_rearm_required")
                S.send("hello")
            with sock, sock.makefile("rb") as f:
                while True:
                    line = f.readline(4098)
                    if not line:
                        raise OSError("EOF")
                    text = line.decode(errors="replace").strip()
                    with (EVID / "serial.log").open("a") as seriallog:
                        seriallog.write(text + "\n")
                    if not text.startswith("M3 "):
                        continue
                    try:
                        row = json.loads(text[3:])
                    except ValueError:
                        continue
                    log("guest", row=row)
                    if not isinstance(row, dict):
                        continue
                    with lock:
                        if row.get("event") == "ready":
                            S.hello_attempts = 0
                            S.stop("guest_ready_rearm_required")
                            S.send("hello")
                            continue
                        if row.get("epoch") != EPOCH:
                            continue
                        if row.get("event") == "timeout":
                            S.stop("guest_timeout")
                            continue
                        if row.get("event") != "ack":
                            continue
                        if type(row.get("seq")) is not int:
                            S.stop("invalid_guest_ack")
                            continue
                        if any(
                            type(row.get(k)) not in (int, float)
                            or not math.isfinite(row[k])
                            or abs(row[k]) > 1
                            for k in ("steer", "throttle")
                        ):
                            S.stop("invalid_guest_ack")
                            continue
                        sent = S.pending.pop(row.get("seq"), None)
                        if not sent:
                            continue
                        delay = time.monotonic() - sent[0]
                        if delay > P["guest_timeout_s"]:
                            S.stop("late_guest_ack")
                            continue
                        if S.ack and row["seq"] <= S.ack["seq"]:
                            continue
                        S.ready = True
                        S.ack = row
                        S.ack["browser_client"] = sent[1].get("browser_client")
                        S.ack["browser_sent_unix_ms"] = sent[1].get(
                            "browser_sent_unix_ms"
                        )
                        S.guest = time.monotonic()
                        log(
                            "ack_correlated",
                            latency_s=delay,
                            command=sent[1],
                            ack=row,
                            pwm_seq=S.pwm_seq,
                        )
        except OSError as e:
            with lock:
                S.serial = None
                S.stop("serial_disconnected")
            log("serial_error", error=str(e))
            time.sleep(0.5)


def issue_ticket():
    now = time.monotonic()
    S.tickets = {k: v for k, v in S.tickets.items() if v > now}
    token = uuid.uuid4().hex
    S.tickets[token] = now + P["browser_timeout_s"]
    return token


def consume_ticket(token):
    if not isinstance(token, str) or S.tickets.pop(token, 0) < time.monotonic():
        raise ValueError("expired or reused command ticket")


def pulse_value(value):
    # PCA's integer pulse quantisation is within ~10 us of configured 1000..2000 us.
    if not 980 <= value <= 2020:
        raise ValueError("PWM outside model calibration")
    return max(-1, min(1, (value - 1500) / 500))


def tick():
    now = time.monotonic()
    with lock:
        if S.mode != "STOPPED":
            try:
                physics_age = (
                    now - json.loads((RUN / "telemetry.json").read_text())["wall"]
                )
            except (OSError, ValueError, KeyError):
                physics_age = 999
            if physics_age > P["bridge_timeout_s"]:
                S.stop("physics_timeout")
            if now - S.browser > P["browser_timeout_s"]:
                S.stop("browser_timeout")
            elif now - S.guest > P["guest_timeout_s"]:
                S.stop("guest_liveness_timeout")
            elif S.pwm is None:
                S.stop("missing_pwm")
        if (
            not S.ready
            and S.serial is not None
            and S.hello_attempts < 3
            and now - S.last_tx >= 1.0
        ):
            S.last_tx = now
            S.send("hello")
        if S.need_stop and S.ready:
            S.send("stop")
            S.need_stop = False
        if (
            S.ready
            and now - S.last_tx >= 0.15
            and not any(now - v[0] < 0.5 for v in S.pending.values())
        ):
            S.last_tx = now
            if S.mode == "ARMING":
                S.send("arm")
            elif S.mode == "ARMED":
                S.send("drive", *S.target)
            else:
                S.send("stop")
        steer = throttle = 0.0
        if S.mode in ("ARMING", "ARMED") and S.pwm and S.ack:
            try:
                a, b = S.pwm["high_us"][:2]
                steer, throttle = pulse_value(a), pulse_value(b)
                # Accept only measured PWM matching the last guest-applied command.
                matched = (
                    abs(steer - S.ack["steer"]) < 0.025
                    and abs(throttle - S.ack["throttle"]) < 0.025
                )
                if not matched:
                    steer = throttle = 0.0
                if abs(throttle) < 0.04:
                    throttle = 0.0
                if abs(steer) < 0.025:
                    steer = 0.0
                if S.mode == "ARMING":
                    steer = throttle = 0.0
                    if (
                        matched
                        and S.ack.get("op") == "arm"
                        and now - S.arm_at > P["arm_dwell_s"]
                    ):
                        S.mode = "ARMED"
                        S.reason = "neutral_arm_confirmed"
                        log("armed", ack_seq=S.ack["seq"], pwm_seq=S.pwm_seq)
            except ValueError:
                S.stop("invalid_pwm")
        if S.mode != "ARMED":
            steer = throttle = 0.0
        atomic(
            RUN / "actuators.json",
            dict(
                epoch=EPOCH,
                wall=now,
                mode=S.mode,
                reason=S.reason,
                steer=steer,
                throttle=throttle,
                pwm_seq=S.pwm_seq,
                ack_seq=(S.ack or {}).get("seq"),
                browser_client=(S.ack or {}).get("browser_client"),
                browser_sent_unix_ms=(S.ack or {}).get("browser_sent_unix_ms"),
                qemu_ns=(S.pwm or {}).get("ns"),
            ),
        )


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, code, data, ctype="application/json"):
        body = json.dumps(data).encode() if ctype == "application/json" else data
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/state":
            with lock:
                try:
                    telemetry = json.loads((RUN / "telemetry.json").read_text())
                except (OSError, ValueError):
                    telemetry = {}
                self.reply(
                    200,
                    dict(
                        epoch=EPOCH,
                        ticket=issue_ticket(),
                        mode=S.mode,
                        reason=S.reason,
                        guest_age_s=time.monotonic() - S.guest,
                        pwm=S.pwm,
                        ack=S.ack,
                        telemetry=telemetry,
                        telemetry_age_s=time.monotonic() - telemetry.get("wall", 0),
                        parameters=P,
                    ),
                )
        elif self.path in ("/", "/app.js"):
            name = "index.html" if self.path == "/" else "app.js"
            self.reply(
                200,
                (ROOT / "m3/web" / name).read_bytes(),
                "text/html" if name.endswith("html") else "text/javascript",
            )
        else:
            self.reply(404, {"error": "not found"})

    def do_POST(self):
        # Same-origin fetch only. No cookies, account credentials or public binding.
        origin = self.headers.get("Origin", "")
        if origin not in (
            "http://" + self.headers.get("Host", ""),
            "https://" + self.headers.get("Host", ""),
        ):
            return self.reply(403, {"error": "same-origin required"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 2048:
                raise ValueError("length")
            c = json.loads(self.rfile.read(length))
            if not isinstance(c, dict):
                raise ValueError("object required")
            if self.path != "/command":
                raise ValueError("path")
            if c.get("epoch") != EPOCH:
                raise ValueError("stale epoch")
            if not isinstance(c.get("client"), str) or len(c["client"]) > 64:
                raise ValueError("client")
            if type(c.get("seq")) is not int:
                raise ValueError("sequence")
            op = c["op"]
            steer = c.get("steer", 0)
            throttle = c.get("throttle", 0)
            if any(
                type(v) not in (int, float) or not math.isfinite(v)
                for v in (steer, throttle)
            ):
                raise ValueError("nonfinite input")
            with lock:
                consume_ticket(c.get("ticket"))
                if op == "stop":
                    S.stop("browser_stop")
                elif (
                    S.client not in (None, c["client"])
                    and time.monotonic() - S.browser < P["browser_timeout_s"]
                ):
                    raise ValueError("another controller owns lease")
                if S.client != c["client"]:
                    S.client = c["client"]
                    S.client_seq = S.client_sequences.get(c["client"], -1)
                if c["seq"] <= S.client_seq:
                    raise ValueError("stale sequence")
                S.client_seq = c["seq"]
                S.client_sequences[c["client"]] = c["seq"]
                S.browser = time.monotonic()
                stamp = c.get("sent_unix_ms")
                S.browser_sent_unix_ms = (
                    stamp
                    if type(stamp) in (int, float) and math.isfinite(stamp)
                    else None
                )
                if op == "arm":
                    if (
                        S.serial is None
                        or S.pwm is None
                        or time.monotonic() - S.guest > 2
                    ):
                        raise ValueError("guest not ready")
                    if abs(steer) > 0 or abs(throttle) > 0:
                        raise ValueError("neutral required")
                    S.mode = "ARMING"
                    S.reason = "arming_neutral"
                    S.arm_at = time.monotonic()
                    S.target = (0, 0)
                    S.send("arm")
                elif op == "drive":
                    if S.mode == "ARMED":
                        S.target = (max(-1, min(1, steer)), max(-1, min(1, throttle)))
                elif op == "stop":
                    pass
                elif (
                    op in ("test_freeze", "test_crash")
                    and os.environ.get("M3_TESTING") == "1"
                ):
                    S.send(op)
                else:
                    raise ValueError("operation")
                log("browser_command", command=c)
            self.reply(200, {"accepted": True})
        except (ValueError, KeyError, TypeError) as e:
            log("rejected_command", error=str(e))
            self.reply(409, {"error": str(e)})


if __name__ == "__main__":
    log("bridge_start")
    for f in (pwm_reader, serial_reader):
        threading.Thread(target=f, daemon=True).start()
    server = ThreadingHTTPServer(("0.0.0.0", 8090), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        while True:
            tick()
            time.sleep(0.02)
    finally:
        with lock:
            S.stop("shutdown")
            tick()
