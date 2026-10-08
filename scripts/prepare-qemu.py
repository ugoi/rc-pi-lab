#!/usr/bin/env python3
from pathlib import Path
import shutil,subprocess
b=Path('build'); q=b/'qemu-10.1.0'
if not q.exists(): subprocess.run(['tar','-xf',str(b/'qemu-10.1.0.tar.xz'),'-C',str(b)],check=True)
for name in ('pca9685.c','pca9685_core.h'): shutil.copyfile(Path('model')/name,q/'hw/i2c'/name)
m=q/'hw/i2c/meson.build';s=m.read_text()
line="i2c_ss.add(when: 'CONFIG_BCM2835_I2C', if_true: files('pca9685.c'))\n"
if line not in s: m.write_text(s.replace('system_ss.add_all',line+'system_ss.add_all'))
(q/'configs/devices/aarch64-softmmu/default.mak').write_text('CONFIG_RASPI=y\nCONFIG_OR_IRQ=y\nCONFIG_UNIMP=y\n')
