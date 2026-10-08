#!/usr/bin/env python3
"""One-way PWM bridge. Unix socket only. Reconnect gets a device snapshot.
Disconnect invalidates output; there is no motor-safety claim for this viewer.
"""
import argparse,json,socket,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('socket');p.add_argument('output');p.add_argument('--seconds',type=float,default=30);a=p.parse_args()
end=time.monotonic()+a.seconds
with open(a.output,'w') as out:
    s=socket.socket(socket.AF_UNIX); s.settimeout(1); s.connect(a.socket)
    out.write(json.dumps({'bridge':'connected','wall_ns':time.time_ns()})+'\n'); out.flush()
    buf=b''
    try:
        while time.monotonic()<end:
            try: data=s.recv(65536)
            except TimeoutError: continue
            if not data: break
            buf+=data
            while b'\n' in buf:
                line,buf=buf.split(b'\n',1)
                try:
                    row=json.loads(line); assert 'high_us' in row and len(row['high_us'])==16
                except (ValueError,AssertionError,KeyError):
                    out.write(json.dumps({'bridge':'framing_error','valid':False})+'\n'); out.flush(); continue
                out.write(json.dumps(row)+'\n');out.flush()
    finally:
        s.close(); out.write(json.dumps({'bridge':'disconnected','valid':False,'wall_ns':time.time_ns()})+'\n')
