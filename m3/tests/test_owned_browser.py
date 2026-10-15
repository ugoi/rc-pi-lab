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
setInterval(()=>document.body.style.background=Date.now()%2000<1000?'white':'gray',100);
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
        self.temp = tempfile.TemporaryDirectory(prefix='m3-client-test-')
        self.evidence = Path(self.temp.name) / 'lifecycle.json'
        self.log = (Path(self.temp.name) / 'stderr.log').open('w+')
        self.proc = None

    def start(self, **overrides):
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
        self.log.close(); self.temp.cleanup()

    def test_input_video_and_repeated_fresh_profiles(self):
        self.start()
        first = self.command('tab', '__owned__')
        self.assertEqual(first['transport'], 'owned-process-pipe')
        self.assertIn('--remote-debugging-pipe', Path(f'/proc/{first["browserPid"]}/cmdline').read_text())
        self.command('open', self.url)
        self.command('record', 'start', str(Path(self.temp.name) / 'live.mp4'))
        self.command('click', '#arm'); self.command('focus', '#throttle'); self.command('press', 'End')
        events = self.command('eval', 'events')['result']
        self.assertTrue(any(e['type']=='keydown' for e in events))
        self.assertTrue(all(e['trusted'] for e in events))
        time.sleep(1.2)
        self.command('record', 'stop')
        subprocess.run(['ffmpeg', '-v', 'error', '-i', str(Path(self.temp.name) / 'live.mp4'),
                        '-f', 'null', '-'], check=True, timeout=10)
        self.finish(); self.proc.stdout.close()
        self.start()
        second = self.command('tab', '__owned__')
        self.assertNotEqual(first['profile'], second['profile'])
        self.assertNotEqual(first['browserPid'], second['browserPid'])
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
        env = dict(os.environ, M3_BROWSER_EVIDENCE=str(Path(self.temp.name)/'missing'/'receipt.json'))
        code = "from browser_client import browser_command,close; import json; print(json.dumps(browser_command(('tab','__owned__'))),flush=True); close()"
        result = subprocess.run([sys.executable, '-c', code], cwd=HERE, env=env,
                                text=True, capture_output=True, timeout=20)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('CDP helper exit', result.stderr)
        info = json.loads(result.stdout)['data']
        self.assertFalse(Path(info['profile']).exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
