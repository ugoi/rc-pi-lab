#!/usr/bin/env python3
"""Bounded real-guest acceptance harness, serial input only (no guest API mocking)."""
import json,os,queue,socket,subprocess,threading,time
from pathlib import Path
log=Path('evidence/boot-stock.log'); lines=queue.Queue()
started=time.monotonic()
p=subprocess.Popen(['sh','scripts/boot-diagnostic.sh'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
def reader():
    with log.open('w') as f:
        for line in p.stdout: f.write(line);f.flush();lines.put(line)
    lines.put(None)
threading.Thread(target=reader,daemon=True).start()
def until(text,timeout=150):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        line=lines.get(timeout=end-time.monotonic())
        if line is None: raise RuntimeError(f'QEMU exited {p.poll()}: waiting {text}')
        if text in line:return line
    raise TimeoutError(text)
def command(cmd):p.stdin.write(cmd+'\n');p.stdin.flush()
def connect():
    s=socket.socket(socket.AF_UNIX);s.settimeout(10);s.connect('build/pwm.sock');return s,s.makefile('r')
def pwm(f,target):
    for _ in range(150):
        row=json.loads(f.readline())
        if row['event'] in ('stop','bridge_open') and abs(row['high_us'][0]-target)<10:return row
    raise AssertionError('missing bridge PWM '+str(target))
try:
    until('APP_PASS')
    cold=time.monotonic()-started
    until('APP_EXIT=0')
    command('python3 -u /opt/rc-lab/device-matrix.py; echo MATRIX_EXIT=$?')
    until('DEVICE_MATRIX_PASS');until('MATRIX_EXIT=0')
    a,af=connect();initial=json.loads(af.readline());assert initial['event']=='bridge_open'
    command('python3 -u /opt/rc-lab/app.py; echo REPEAT_EXIT=$?')
    before=pwm(af,1000)
    af.close();a.close()
    until('ANGLE 90');time.sleep(.2)
    b,bf=connect();snapshot=json.loads(bf.readline());assert snapshot['event']=='bridge_open'
    after=pwm(bf,2000)
    off=pwm(bf,0)
    bf.close();b.close()
    until('REPEAT_EXIT=0')
    Path('evidence/bridge-test.json').write_text(json.dumps(dict(result='PASS',cold_boot_app_seconds=cold,before_disconnect=before,reconnect_snapshot=snapshot,after_reconnect=after,full_off=off),indent=2)+'\n')
    print('PASS guest app, device matrix, disconnect/reconnect; seconds',round(time.monotonic()-started,2),flush=True)
    command('sync')
finally:
    p.terminate()
    try:p.wait(timeout=10)
    except subprocess.TimeoutExpired:p.kill();p.wait()
