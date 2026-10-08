#!/usr/bin/env python3
"""Cold-boot the complete SD image with original systemd and a bounded deadline."""
import subprocess,time,json
from pathlib import Path
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
Path('evidence/image-boot-result.json').write_text(json.dumps({'result':'PASS','wall_seconds':time.monotonic()-start,'qemu_exit':code},indent=2)+'\n')
