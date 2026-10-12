import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from actuator_state import effective_control


class Tests(unittest.TestCase):
    def setUp(self):
        self.source = dict(
            wall=10, mode="ARMED", reason="neutral_arm_confirmed", steer=0.2, throttle=1
        )

    def test_stale_armed_input_reports_actual_stop(self):
        out = effective_control(self.source, 10.565, 0.5)
        self.assertEqual(
            (out["mode"], out["reason"], out["throttle"]),
            ("STOPPED", "bridge_timeout", 0),
        )
        self.assertEqual(out["source_status"], "stale")
        self.assertEqual(self.source["mode"], "ARMED")  # historical record retained

    def test_missing_file_cannot_reuse_previous_input(self):
        self.assertTrue(effective_control(self.source, 10.1, 0.5)["active"])
        out = effective_control(None, 10.2, 0.5)
        self.assertEqual((out["reason"], out["throttle"]), ("bridge_disconnected", 0))

    def test_invalid_clock_or_actuator_stops(self):
        for patch in (
            {"wall": 12},
            {"wall": float("nan")},
            {"throttle": float("inf")},
            {"mode": "unknown"},
            {"steer": None},
        ):
            out = effective_control(dict(self.source, **patch), 10.1, 0.5)
            self.assertFalse(out["active"])
            self.assertEqual(out["reason"], "invalid_actuator_data")

    def test_fresh_drive_and_explicit_stop(self):
        self.assertEqual(effective_control(self.source, 10.1, 0.5)["throttle"], 1)
        out = effective_control(
            dict(self.source, mode="STOPPED", reason="browser_stop"), 10.1, 0.5
        )
        self.assertEqual((out["reason"], out["throttle"]), ("browser_stop", 0))


if __name__ == "__main__":
    unittest.main()
