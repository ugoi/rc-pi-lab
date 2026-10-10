import importlib.util, json, os, unittest, time, tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("bridge", root / "m3/bridge.py")
b = importlib.util.module_from_spec(spec)
os.environ["M3_RUN_DIR"] = tempfile.mkdtemp(prefix="m3-unit-run-")
os.environ["M3_EVIDENCE_DIR"] = tempfile.mkdtemp(prefix="m3-unit-evidence-")
spec.loader.exec_module(b)
b.RUN = Path(tempfile.mkdtemp(prefix="m3-unit-"))


class FakeSerial:
    def __init__(self):
        self.messages = []

    def send(self, raw, flags):
        self.messages.append(json.loads(raw))
        return len(raw)


class Tests(unittest.TestCase):
    def setUp(self):
        b.S = b.State()
        b.S.serial = FakeSerial()

    def arm(self):
        b.atomic(b.RUN / "telemetry.json", {"wall": time.monotonic()})
        s = b.S
        s.ready = True
        s.mode = "ARMED"
        s.browser = s.guest = time.monotonic()
        s.pwm = {"seq": 4, "ns": 123, "high_us": [1500, 1750] + [0] * 14}
        s.ack = {"seq": 2, "op": "drive", "steer": 0, "throttle": 0.5}
        return s

    def test_held_pwm_does_not_keep_guest_alive(self):
        s = self.arm()
        s.guest -= 1
        b.tick()
        self.assertEqual(s.mode, "STOPPED")
        self.assertEqual(
            json.loads((b.RUN / "actuators.json").read_text())["throttle"], 0
        )

    def test_browser_loss_latches(self):
        s = self.arm()
        s.browser -= 1
        b.tick()
        s.browser = s.guest = time.monotonic()
        b.tick()
        self.assertEqual(s.mode, "STOPPED")

    def test_drive_comes_from_pwm_not_target(self):
        s = self.arm()
        s.target = (1, 1)
        b.tick()
        a = json.loads((b.RUN / "actuators.json").read_text())
        self.assertEqual(a["throttle"], 0.5)
        self.assertEqual(a["steer"], 0)

    def test_unmatched_pwm_cannot_drive(self):
        s = self.arm()
        s.pwm["high_us"][1] = 2000
        b.tick()
        self.assertEqual(
            json.loads((b.RUN / "actuators.json").read_text())["throttle"], 0
        )

    def test_invalid_pwm_latches(self):
        s = self.arm()
        s.pwm["high_us"][1] = 0
        b.tick()
        self.assertEqual(s.mode, "STOPPED")

    def test_boot_does_not_flood_serial(self):
        b.tick()
        b.tick()
        self.assertEqual([c["op"] for c in b.S.serial.messages], ["hello"])

    def test_nonblocking_backpressure_stops(self):
        s = self.arm()

        def blocked(*args):
            raise BlockingIOError()

        s.serial.send = blocked
        s.send("drive", 0, 0.5)
        self.assertEqual(s.mode, "STOPPED")
        self.assertIsNone(s.serial)

    def test_arm_waits_for_neutral_ack(self):
        s = self.arm()
        s.mode = "ARMING"
        s.arm_at = time.monotonic() - 1
        b.tick()
        self.assertEqual(s.mode, "ARMING")

    def test_handshake_retry_is_bounded(self):
        for _ in range(12):
            b.S.last_tx = 0
            b.tick()
        self.assertEqual(len(b.S.serial.messages), 3)
        self.assertTrue(all(c["op"] == "hello" for c in b.S.serial.messages))

    def test_freshness_ticket_once_only(self):
        ticket = b.issue_ticket()
        b.consume_ticket(ticket)
        with self.assertRaises(ValueError):
            b.consume_ticket(ticket)

    def test_expired_ticket_rejected(self):
        b.S.tickets["old"] = time.monotonic() - 1
        with self.assertRaises(ValueError):
            b.consume_ticket("old")

    def test_calibration(self):
        self.assertAlmostEqual(b.pulse_value(1498.16), -0.00368)
        for x in [None, "1500", float("nan"), 0, 3000]:
            with self.assertRaises((TypeError, ValueError)):
                b.pulse_value(x)


if __name__ == "__main__":
    unittest.main()
