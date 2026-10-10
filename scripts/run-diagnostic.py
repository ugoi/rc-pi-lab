#!/usr/bin/env python3
"""Bounded real-guest acceptance; readiness comes from the unchanged guest app."""
import json
import queue
import re
import socket
import subprocess
import threading
import time
from pathlib import Path

from pwm_protocol import decode_frame

TOTAL_SECONDS = 900
START_SECONDS = 60
RUN_SECONDS = 45


class Stream:
    """Drain continuously, including while the harness waits on the other stream.

    Each observation carries its host receipt time. Deadlines apply to the whole
    phase, never reset on unrelated events or partial data.
    """
    def __init__(self, source, log=None, decoder=lambda line: line.rstrip()):
        self.events = queue.Queue()
        self.last = None
        self.source = source
        self.log = log
        self.decoder = decoder
        self.thread = threading.Thread(target=self._read, daemon=True)
        self.thread.start()

    def _read(self):
        try:
            for line in self.source:
                received = time.monotonic()
                if self.log:
                    self.log.write(line)
                    self.log.flush()
                self.events.put((received, self.decoder(line)))
        except (OSError, ValueError) as exc:
            self.events.put((time.monotonic(), exc))
        finally:
            self.events.put((time.monotonic(), None))

    def until(self, predicate, deadline, label):
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f'{label}: deadline exceeded; last={self.last!r}')
            try:
                received, value = self.events.get(timeout=remaining)
            except queue.Empty as exc:
                raise TimeoutError(f'{label}: deadline exceeded; last={self.last!r}') from exc
            if value is None:
                raise RuntimeError(f'{label}: stream EOF; last={self.last!r}')
            if isinstance(value, Exception):
                raise RuntimeError(f'{label}: stream error: {value}') from value
            self.last = value
            if isinstance(value, str) and ('Kernel panic' in value or
                    re.search(r'(?:APP|MATRIX|REPEAT)_EXIT=[1-9]', value)):
                raise RuntimeError(f'{label}: guest failure: {value}')
            if predicate(value):
                return received, value


def main():
    started = time.monotonic()
    overall = started + TOTAL_SECONDS
    timings = {}
    peers = []
    result = {'result': 'FAIL', 'budgets_seconds': {
        'total': TOTAL_SECONDS, 'startup': START_SECONDS, 'repeat_run': RUN_SECONDS}}
    with Path('evidence/boot-stock.log').open('w') as log:
        process = subprocess.Popen(['sh', 'scripts/boot-diagnostic.sh'],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, bufsize=1)
        serial = Stream(process.stdout, log)

        def deadline(seconds):
            return min(overall, time.monotonic() + seconds)

        def until(text, end):
            # Anchor lines so echoed shell commands cannot fake readiness or PASS.
            return serial.until(lambda line: line.strip() == text, end, text)

        def angle_ready(angle, end):
            return serial.until(lambda line: bool(re.fullmatch(
                rf'ANGLE {angle} monotonic_ns [0-9]+', line.strip())), end,
                f'guest ANGLE {angle} readiness')

        def command(cmd):
            process.stdin.write(cmd + '\n')
            process.stdin.flush()

        def connect(end):
            peer = socket.socket(socket.AF_UNIX)
            peers.append(peer)
            peer.settimeout(max(0.001, end - time.monotonic()))
            peer.connect('build/pwm.sock')
            peer.settimeout(None)  # Reader drains; Stream.until owns the deadline.
            file = peer.makefile('rb')
            stream = Stream(file, decoder=decode_frame)
            stamp, row = stream.until(lambda row: row['event'] == 'bridge_open',
                                      end, 'fresh bridge_open snapshot')
            return peer, file, stream, stamp, row

        def pwm(stream, target, after_seq, end):
            return stream.until(lambda row: row['seq'] > after_seq and
                row['event'] == 'stop' and abs(row['high_us'][0] - target) < 10,
                end, f'PWM {target} after seq {after_seq}')

        def close(peer, file, stream):
            peer.shutdown(socket.SHUT_RDWR)
            stream.thread.join(timeout=1)
            file.close()
            peer.close()
            peers.remove(peer)

        try:
            first_ready, _ = angle_ready(0, deadline(600))
            timings['cold_ready_seconds'] = first_ready - started
            until('APP_PASS', deadline(RUN_SECONDS))
            until('APP_EXIT=0', deadline(5))
            timings['cold_boot_app_seconds'] = time.monotonic() - started
            command('python3 -u /opt/rc-lab/device-matrix.py; echo MATRIX_EXIT=$?')
            matrix_end = deadline(START_SECONDS)
            until('DEVICE_MATRIX_PASS', matrix_end)
            until('MATRIX_EXIT=0', matrix_end)

            peer, file, stream, _, initial = connect(deadline(5))
            issued = time.monotonic()
            # Marker separates shell dispatch from Python import/ServoKit startup.
            command("printf '\\nRC_REPEAT_BEGIN\\n'; python3 -u /opt/rc-lab/app.py; echo REPEAT_EXIT=$?")
            startup_end = deadline(START_SECONDS)
            dispatched, _ = until('RC_REPEAT_BEGIN', startup_end)
            ready, _ = angle_ready(0, startup_end)
            run_end = deadline(RUN_SECONDS)
            observed, before = pwm(stream, 1000, initial['seq'], run_end)
            timings.update(repeat_dispatch_seconds=dispatched-issued,
                           repeat_ready_seconds=ready-issued,
                           repeat_first_pwm_seconds=observed-issued,
                           ready_to_pwm_seconds=observed-ready)
            close(peer, file, stream)
            angle_ready(90, run_end)
            peer, file, stream, _, snapshot = connect(min(run_end, deadline(5)))
            if snapshot['seq'] <= before['seq']:
                raise AssertionError('reconnect snapshot is stale')
            _, after = pwm(stream, 2000, snapshot['seq'], run_end)
            _, off = pwm(stream, 0, after['seq'], run_end)
            close(peer, file, stream)
            until('APP_PASS', run_end)
            until('REPEAT_EXIT=0', run_end)
            command('sync; mount -o remount,ro /dev/mmcblk0 /; echo DISK_CLEAN=$?')
            until('DISK_CLEAN=0', deadline(60))
            result.update(result='PASS', before_disconnect=before,
                          reconnect_snapshot=snapshot, after_reconnect=after, full_off=off)
        except Exception as exc:
            result['error'] = f'{type(exc).__name__}: {exc}'
            raise
        finally:
            for peer in peers:
                try:
                    peer.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                peer.close()
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            serial.thread.join(timeout=2)
            process.stdin.close()
            process.stdout.close()
            result.update(timings=timings, total_seconds=time.monotonic()-started)
            Path('evidence/bridge-test.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
