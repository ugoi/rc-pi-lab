"""Host regressions: malformed wire input, reconnect, readiness deadlines.
These tests do not claim Linux/I2C acceptance; run-diagnostic.py provides that.
"""
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from pwm_protocol import decode_frame
spec = importlib.util.spec_from_file_location('diagnostic', ROOT / 'scripts/run-diagnostic.py')
diagnostic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnostic)
ROW = dict(seq=1, ns=0, event='bridge_open', reg=-1, value=-1,
           mode1=17, mode2=4, prescale=30, period_us=5079.04, high_us=[0.0]*16)


class ProtocolTests(unittest.TestCase):
    def test_original_samples(self):
        evidence = json.loads((ROOT / 'evidence/bridge-test.json').read_text())
        for key in ['before_disconnect', 'reconnect_snapshot', 'after_reconnect', 'full_off']:
            row = evidence[key]
            self.assertEqual(decode_frame(json.dumps(row)), row)

    def test_invalid_shapes_and_numbers(self):
        cases = [None, [], True, 12, 'bad', {}, {'high_us': None},
                 {'high_us': ['broken']*16}]
        for field, bads in {
            'high_us': [None, [], [0]*15, [0]*17, ['0']*16, [True]*16,
                        [float('nan')]*16, [float('inf')]*16, [-1]*16, [6000]*16],
            'period_us': ['5079', None, True, float('nan'), float('inf'), -1, 0],
            'ns': [None, True, -1, 1.5], 'seq': [0, -1, True, '1'],
            'event': [[], None, 'made_up'], 'prescale': [2, 256, True],
            'reg': [-2, 256, True], 'value': [None], 'mode1': [False],
            'mode2': [float('nan')],
        }.items():
            for bad in bads:
                row = copy.deepcopy(ROW); row[field] = bad; cases.append(row)
        extra = dict(ROW, unexpected=float('nan')); cases.append(extra)
        for row in cases:
            with self.subTest(row=row), self.assertRaises(ValueError):
                decode_frame(json.dumps(row))
        for data in [b'{', b'\xff', b'['*2000, b' '*4097]:
            with self.subTest(data=data[:15]), self.assertRaises(ValueError):
                decode_frame(data)


class ConsumerTests(unittest.TestCase):
    def run_peer(self, directory, payload, name):
        path = Path(directory) / 'peer.sock'
        path.unlink(missing_ok=True)
        server = socket.socket(socket.AF_UNIX)
        server.bind(str(path)); server.listen(1); server.settimeout(5)
        failures = []
        def send():
            try:
                peer, _ = server.accept()
                with peer:
                    # Split within frames: stream chunking is not message framing.
                    peer.sendall(payload[:7]); peer.sendall(payload[7:])
            except Exception as exc:
                failures.append(exc)
            finally:
                server.close()
        thread = threading.Thread(target=send); thread.start()
        output = Path(directory) / (name + '.jsonl')
        process = subprocess.run([sys.executable, str(ROOT/'scripts/bridge.py'),
                                  str(path), str(output), '--seconds', '2'],
                                 capture_output=True, text=True, timeout=5)
        thread.join(timeout=5)
        self.assertFalse(thread.is_alive()); self.assertFalse(failures)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertNotIn('Traceback', process.stderr)
        rows = [json.loads(line) for line in output.read_text().splitlines()]
        self.assertEqual(rows[-1]['bridge'], 'disconnected')
        self.assertIs(rows[-1]['valid'], False)
        return rows

    def test_qa_failures_then_valid_trace_and_restart(self):
        evidence = json.loads((ROOT/'evidence/bridge-test.json').read_text())
        trace = [evidence[key] for key in ['before_disconnect', 'reconnect_snapshot',
                                         'after_reconnect', 'full_off']]
        bads = [None, {'high_us': None}, {'high_us': ['broken']*16}]
        bads += [dict(ROW, high_us=[v]*16) for v in [True, float('nan'), float('inf')]]
        payload = b''.join(json.dumps(row).encode()+b'\n' for row in bads+trace)
        with tempfile.TemporaryDirectory() as directory:
            rows = self.run_peer(directory, payload, 'first')
            self.assertEqual([r for r in rows if 'high_us' in r], trace)
            self.assertEqual(sum(r.get('bridge') == 'framing_error' for r in rows), len(bads))
            # Explicit consumer restart gets a fresh QEMU-shaped snapshot, not old state.
            rows = self.run_peer(directory, json.dumps(ROW).encode()+b'\n', 'restart')
            self.assertEqual([r for r in rows if 'high_us' in r], [ROW])

    def test_truncated_and_oversized_frames(self):
        with tempfile.TemporaryDirectory() as directory:
            for i, data in enumerate([b'{"high_us":', b'x'*4097, b'x'*4097+b'\n']):
                rows = self.run_peer(directory, data, str(i))
                self.assertTrue(any(r.get('bridge') == 'framing_error' for r in rows))
                self.assertFalse(any('high_us' in r for r in rows))

    def test_stale_frame_invalidates_state(self):
        with tempfile.TemporaryDirectory() as directory:
            row = json.dumps(ROW).encode()+b'\n'
            rows = self.run_peer(directory, row+row, 'stale')
            self.assertEqual(sum('high_us' in r for r in rows), 1)
            self.assertEqual(rows[-2]['bridge'], 'framing_error')


class ReadinessTests(unittest.TestCase):
    def test_whole_harness_missing_readiness_has_finite_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'scripts').mkdir(); (root/'evidence').mkdir()
            (root/'scripts/boot-diagnostic.sh').write_text('echo AUDIT_START\nexec sleep 20\n')
            previous = Path.cwd()
            started = time.monotonic()
            try:
                os.chdir(root)
                with patch.object(diagnostic, 'TOTAL_SECONDS', 0.2):
                    with self.assertRaisesRegex(TimeoutError, 'ANGLE 0 readiness: deadline'):
                        diagnostic.main()
                result = json.loads((root/'evidence/bridge-test.json').read_text())
                self.assertEqual(result['result'], 'FAIL')
                self.assertIn('AUDIT_START', result['error'])
                self.assertLess(time.monotonic()-started, 3)
            finally:
                os.chdir(previous)

    def test_echo_is_not_readiness_and_eof_is_not_pass(self):
        stream = diagnostic.Stream(io.StringIO('echo RC_REPEAT_BEGIN\n'))
        with self.assertRaisesRegex(RuntimeError, 'stream EOF'):
            stream.until(lambda s: s == 'RC_REPEAT_BEGIN', time.monotonic()+1, 'dispatch')

    def test_unrelated_events_do_not_extend_deadline(self):
        stream = diagnostic.Stream(io.StringIO('other\n'*100000))
        started = time.monotonic()
        with self.assertRaises(TimeoutError):
            stream.until(lambda s: s == 'READY', started+0.01, 'readiness')
        self.assertLess(time.monotonic()-started, 1)
        stream.thread.join(timeout=2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
