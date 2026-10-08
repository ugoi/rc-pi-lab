#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
names=['guest/app.py','guest/requirements.lock','model/pca9685.c','model/pca9685_core.h',
       'build/boot/kernel8.img','build/boot/bcm2710-rpi-3-b.dtb','build/boot/qemu-rpi3.dtb']
rows={n:hashlib.sha256(Path(n).read_bytes()).hexdigest() for n in names}
Path('evidence/component-sha256.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2))
