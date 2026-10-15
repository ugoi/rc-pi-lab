"""Real-process isolation/lifecycle checks on a local fixture, not Pi acceptance.

Requires the pinned M3_BROWSER_EXECUTABLE/SHA256. No shared-browser connection.
"""
import http.server
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest

HERE = Path(__file__).resolve().parent
HTML = b'''<button id="arm">Start</button><input id="throttle" type="range">
<script>window.events=[];for(const name of ['click','keydown'])
document.addEventListener(name,e=>events.push({type:e.type,trusted:e.isTrusted}));
let n=0;setInterval(()=>{document.body.style.background=n++%2?'white':'gray'},100);
</script>'''


class Fixture(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(HTML)

    def log_message(self, *_args):
        pass


class BrowserIsolation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Fixture)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close()

    def setUp(self):
        base = Path(os.environ.get('M3_BROWSER_TEST_EVIDENCE',
                    str(HERE.parents[1] / 'evidence/m3/browser-process-tests')))
        base.mkdir(parents=True, exist_ok=True)
        self.directory = Path(tempfile.mkdtemp(prefix=self._testMethodName+'-', dir=base))
        self.evidence = self.directory / 'lifecycle-1.json'
        self.log = (self.directory / 'stderr.log').open('w+')
        self.proc = None
        self.starts = 0

    def start(self, **overrides):
        self.starts += 1
        self.evidence = self.directory / f'lifecycle-{self.starts}.json'
        env = dict(os.environ, M3_BROWSER_EVIDENCE=str(self.evidence), **overrides)
        self.proc = subprocess.Popen(['node', str(HERE / 'browser_cdp.mjs')],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.log,
            text=True, env=env)

    def send(self, *args):
        self.proc.stdin.write(json.dumps(args)+'\n'); self.proc.stdin.flush()

    def receive(self):
        self.assertTrue(select.select([self.proc.stdout], [], [], 12)[0], 'client deadline')
        line = self.proc.stdout.readline()
        self.assertTrue(line, 'client exited before response')
        return json.loads(line)

    def command(self, *args):
        self.send(*args)
        response = self.receive()
        self.assertTrue(response['success'], response)
        return response['data']

    def finish(self, code=0):
        self.proc.stdin.close()
        self.assertEqual(self.proc.wait(timeout=8), code)
        result = json.loads(self.evidence.read_text())
        self.assertEqual(result['remainingPids'], [])
        self.assertTrue(result['profileRemoved'])
        self.assertFalse(Path(result['profile']).exists())

    def tearDown(self):
        if self.proc:
            if self.proc.poll() is None:
                self.proc.terminate()
                self.proc.wait(timeout=8)
            if not self.proc.stdin.closed: self.proc.stdin.close()
            self.proc.stdout.close()
        self.log.close()

    def test_input_and_live_video(self):
        self.start()
        first = self.command('tab', '__owned__')
        self.assertEqual(first['transport'], 'owned-process-pipe')
        self.assertIn('--remote-debugging-pipe', Path(f'/proc/{first["browserPid"]}/cmdline').read_text())
        self.command('open', self.url)
        first_frames = self.command('record', 'start', str(self.directory / 'live.mp4'))['frames']
        self.command('click', '#arm'); self.command('focus', '#throttle'); self.command('press', 'End')
        events = self.command('eval', 'events')['result']
        self.assertTrue(any(e['type']=='keydown' for e in events))
        self.assertTrue(all(e['trusted'] for e in events))
        observed = self.command('record', 'wait_frames', str(first_frames + 2))
        self.assertGreaterEqual(observed['frames'], first_frames + 2)
        result = self.command('record', 'stop')
        receipt = json.loads((self.directory / 'live.mp4.timestamps.json').read_text())
        self.assertEqual(receipt['status'], 'encoded')
        self.assertEqual(receipt['frameCount'], result['frames'])
        self.assertGreater(receipt['frames'][-1]['timestamp'], receipt['frames'][0]['timestamp'])
        subprocess.run(['ffmpeg', '-v', 'error', '-i', str(self.directory / 'live.mp4'),
                        '-f', 'null', '-'], check=True, timeout=10)
        self.finish()

    def test_repeated_fresh_profiles(self):
        self.start()
        first = self.command('tab', '__owned__')
        self.finish(); self.proc.stdout.close()
        self.start()
        second = self.command('tab', '__owned__')
        self.assertNotEqual(first['profile'], second['profile'])
        self.assertNotEqual(first['browserPid'], second['browserPid'])
        self.finish()

    def test_recording_deadline_keeps_frame_evidence(self):
        self.start(); self.command('open', self.url)
        self.command('record', 'start', str(self.directory / 'incomplete.mp4'))
        start = time.monotonic()
        self.send('record', 'wait_frames', '10000')
        response = self.receive()
        self.assertFalse(response['success'])
        self.assertIn('recording deadline', response['error'])
        self.assertLess(time.monotonic()-start, 5)
        receipt = json.loads((self.directory / 'incomplete.mp4.timestamps.json').read_text())
        self.assertEqual(receipt['status'], 'incomplete')
        self.assertEqual(receipt['frameCount'], len(receipt['frames']))
        self.assertGreater(receipt['frameCount'], 0)
        self.assertLess(receipt['frameCount'], 10000)
        self.finish()

    def test_sigterm_during_pending_command_cleans_processes(self):
        self.start(); self.command('tab', '__owned__')
        self.send('eval', 'new Promise(()=>{})')
        time.sleep(.2)
        self.proc.send_signal(signal.SIGTERM)
        self.finish(code=143)

    def test_browser_crash_fails_promptly_and_cleans_profile(self):
        self.start(); info = self.command('tab', '__owned__')
        self.send('eval', 'new Promise(()=>{})')
        time.sleep(.2); start = time.monotonic()
        os.kill(info['browserPid'], signal.SIGKILL)
        response = self.receive()
        self.assertFalse(response['success'])
        self.assertLess(time.monotonic()-start, 3)
        self.finish()

    def test_external_target_rejected_before_browser_launch(self):
        self.start(M3_BROWSER_TARGET='personal-target')
        self.assertNotEqual(self.proc.wait(timeout=3), 0)
        self.assertFalse(self.evidence.exists())

    def test_changed_binary_rejected_before_browser_launch(self):
        self.start(M3_BROWSER_SHA256='0'*64)
        self.assertNotEqual(self.proc.wait(timeout=8), 0)
        self.assertFalse(self.evidence.exists())

    def test_python_wrapper_rejects_missing_cleanup_receipt(self):
        # Real browser/driver; the nonexistent evidence parent makes the cleanup
        # receipt fail after process cleanup. The caller must fail, not pass.
        env = dict(os.environ, M3_BROWSER_EVIDENCE=str(self.directory/'missing'/'receipt.json'))
        code = "from browser_client import browser_command,close; import json; print(json.dumps(browser_command(('tab','__owned__'))),flush=True); close()"
        result = subprocess.run([sys.executable, '-c', code], cwd=HERE, env=env,
                                text=True, capture_output=True, timeout=20)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('CDP helper exit', result.stderr)
        info = json.loads(result.stdout)['data']
        self.assertFalse(Path(info['profile']).exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
