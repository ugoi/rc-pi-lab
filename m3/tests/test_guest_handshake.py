"""PTY protocol regression running the actual app; ServoKit is a host stub, not I2C proof."""

import json, os, pty, select, subprocess, sys, tempfile, time, unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "guest_control.py"


class TestGuest(unittest.TestCase):
    def test_idle_beacons_allow_new_bridge_epoch(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "adafruit_servokit.py").write_text("""
class Servo:
    angle = 90
    def set_pulse_width_range(self, *args): pass
class ServoKit:
    def __init__(self, **kw): self.servo = [Servo(), Servo()]
""")
            master, slave = pty.openpty()
            proc = subprocess.Popen(
                [sys.executable, "-u", str(APP)],
                stdin=slave,
                stdout=slave,
                stderr=slave,
                env={**os.environ, "PYTHONPATH": tmp},
            )
            os.close(slave)
            buf = b""

            def event(kind, timeout=3):
                nonlocal buf
                end = time.monotonic() + timeout
                while time.monotonic() < end:
                    if b"\n" not in buf:
                        if not select.select(
                            [master], [], [], max(0, end - time.monotonic())
                        )[0]:
                            break
                        buf += os.read(master, 4096)
                    while b"\n" in buf:
                        line, buf = buf.split(b"\n", 1)
                        if line.startswith(b"M3 "):
                            row = json.loads(line[3:])
                            if row["event"] == kind:
                                return row
                self.fail("missing " + kind)

            def send(epoch, seq, op):
                os.write(
                    master,
                    (
                        json.dumps(
                            dict(epoch=epoch, seq=seq, op=op, steer=0, throttle=0)
                        )
                        + "\n"
                    ).encode(),
                )

            try:
                first = event("ready")
                second = event("ready")
                self.assertGreaterEqual(
                    second["guest_ns"] - first["guest_ns"], 1_000_000_000
                )
                send("a" * 32, 1, "hello")
                ack = event("ack")
                self.assertEqual(
                    (ack["epoch"], ack["armed"], ack["throttle"]), ("a" * 32, False, 0)
                )
                send("a" * 32, 2, "arm")
                self.assertTrue(event("ack")["armed"])
                event("timeout")
                event("ready")
                send("b" * 32, 1, "hello")
                ack = event("ack")
                self.assertEqual(
                    (ack["epoch"], ack["seq"], ack["armed"]), ("b" * 32, 1, False)
                )
            finally:
                proc.terminate()
                proc.wait(timeout=3)
                os.close(master)


if __name__ == "__main__":
    unittest.main()
