#!/usr/bin/env python3
"""Cold-boot the complete SD image with original systemd and a bounded deadline."""
import subprocess,time,json,os,hashlib,re
from pathlib import Path
def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(8*1024**2),b''):h.update(chunk)
    return h.hexdigest()
immutable=os.environ.get('SNAPSHOT')=='1'
before=digest('build/rc-pi3.img') if immutable else None
start=time.monotonic()
with Path('evidence/boot-image.log').open('w') as log:
    p=subprocess.Popen(['sh','scripts/boot-image.sh'],stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
    try:
        code=p.wait(timeout=1200)
    except subprocess.TimeoutExpired:
        p.terminate();p.wait(timeout=10);raise
text=Path('evidence/boot-image.log').read_text(errors='replace')
assert code==0, code
assert 'SYSTEMD_DEMO_PASS' in text and 'Power down' in text, 'Guest did not pass and power off'
subprocess.run(['python3','tests/validate_trace.py','evidence/pca-image.jsonl','evidence/boot-image.log'],check=True)
after=digest('build/rc-pi3.img') if immutable else None
assert before==after, 'Snapshot boot modified base image'
clean=re.sub(r'\x1b\[[0-9;]*[A-Za-z]','',text)
failures=[line for line in clean.splitlines() if '[FAILED]' in line or '[DEPEND]' in line]
Path('evidence/image-boot-result.json').write_text(json.dumps({'result':'PASS_SCOPED_SERVO_PATH','wall_seconds':time.monotonic()-start,'qemu_exit':code,'snapshot':immutable,'base_sha256_before':before,'base_sha256_after':after,'ancillary_boot_failures':failures},indent=2)+'\n')
