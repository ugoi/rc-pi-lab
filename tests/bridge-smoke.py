#!/usr/bin/env python3
"""Actual QEMU callback regression: disconnect must not deadlock its main loop.
This is a device test without a guest; it does not replace the Linux guest test.
"""
import json,socket,subprocess,time
from pathlib import Path
qmp=Path('build/bridge-smoke-qmp.sock');pwm=Path('build/bridge-smoke-pwm.sock')
for path in (qmp,pwm):path.unlink(missing_ok=True)
p=subprocess.Popen(['build/qemu-out/qemu-system-aarch64','-M','raspi3b','-S',
 '-display','none','-serial','null','-monitor','none',
 '-qmp',f'unix:{qmp},server=on,wait=off',
 '-chardev',f'socket,id=pwm,path={pwm},server=on,wait=off',
 '-device','pca9685,bus=i2c-bus.1,address=0x40,chardev=pwm'],
 stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
def connect(path):
 s=socket.socket(socket.AF_UNIX);s.settimeout(5);s.connect(str(path));return s
try:
 deadline=time.monotonic()+10
 while not qmp.exists() or not pwm.exists():
  assert p.poll() is None,p.stderr.read().decode()
  assert time.monotonic()<deadline,'socket creation timeout'
  time.sleep(.05)
 control=connect(qmp);f=control.makefile('rwb');assert 'QMP' in json.loads(f.readline())
 def query(name):
  f.write((json.dumps({'execute':name})+'\n').encode());f.flush()
  while True:
   result=json.loads(f.readline())
   if 'return' in result:return result['return']
   assert 'error' not in result,result
 query('qmp_capabilities');snapshots=[]
 for _ in range(3):
  s=connect(pwm);stream=s.makefile('rb');row=json.loads(stream.readline())
  assert row['event']=='bridge_open';snapshots.append(row['seq'])
  stream.close();s.close();time.sleep(.1)
  assert query('query-status')['running'] is False
 assert snapshots==sorted(set(snapshots)),snapshots
 query('quit');p.wait(timeout=5)
 result={'result':'PASS','open_snapshot_sequences':snapshots,'disconnect_cycles':3,'layer':'QEMU device, no guest'}
 Path('evidence/bridge-device-smoke.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
finally:
 if p.poll() is None:
  p.kill();p.wait()
 for path in (qmp,pwm):path.unlink(missing_ok=True)
