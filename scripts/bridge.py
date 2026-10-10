#!/usr/bin/env python3
"""Bounded PWM observer. Invalid input and disconnect invalidate the last state."""
import argparse
import json
import math
import socket
import time

from pwm_protocol import MAX_FRAME, decode_frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('socket')
    parser.add_argument('output')
    parser.add_argument('--seconds', type=float, default=30)
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or args.seconds <= 0:
        parser.error('--seconds must be finite and positive')
    deadline = time.monotonic() + args.seconds
    with open(args.output, 'w') as out, socket.socket(socket.AF_UNIX) as peer:
        def emit(row):
            out.write(json.dumps(row, allow_nan=False) + '\n')
            out.flush()

        def status(kind, reason=None):
            row = {'bridge': kind, 'valid': False, 'wall_ns': time.time_ns()}
            if reason:
                row['reason'] = reason
            emit(row)

        buf = b''
        reason = 'deadline'
        last_seq = 0
        try:
            peer.settimeout(min(1, args.seconds))
            peer.connect(args.socket)
            status('connected')  # Not a PWM sample yet.
            while time.monotonic() < deadline:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                peer.settimeout(min(1, remaining))
                try:
                    data = peer.recv(65536)
                except TimeoutError:
                    continue
                if not data:
                    reason = 'eof'
                    break
                buf += data
                while b'\n' in buf:
                    line, buf = buf.split(b'\n', 1)
                    try:
                        row = decode_frame(line)
                        if row['seq'] <= last_seq:
                            raise ValueError('non-increasing seq')
                    except ValueError as exc:
                        status('framing_error', str(exc))
                        continue  # Next complete valid frame restores observations.
                    last_seq = row['seq']
                    emit(row)
                if len(buf) > MAX_FRAME:
                    # No delimiter: cannot resynchronise within the bounded frame size.
                    status('framing_error', 'unterminated oversized frame')
                    buf = b''
                    reason = 'oversized_frame'
                    break
            if buf:
                status('framing_error', 'incomplete frame at stream end')
        except OSError as exc:
            reason = f'socket_error: {exc}'
        finally:
            status('disconnected', reason)
    # Reconnection is an explicit new invocation, with a new bridge_open snapshot.


if __name__ == '__main__':
    main()
