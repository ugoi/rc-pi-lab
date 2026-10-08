#!/usr/bin/env python3
"""Convert the tested task-owned rootfs to a full SD image in place to limit disk use.
This destroys ONLY that intermediate rootfs; original compressed image is retained.
Run only with QEMU stopped. Needs ~1 GiB additional free disk space.
"""
import lzma,os,shutil,subprocess,fcntl
from pathlib import Path
root=Path('build/rootfs.img'); target=Path('build/rc-pi3.img')
assert root.exists() and not target.exists()
assert shutil.disk_usage(root.parent).free > 1200*1024**2, 'Need at least 1200 MiB additional disk headroom'
# Reject concurrent QEMU access before modifying this task-owned image.
locked=root.open('r+b');fcntl.lockf(locked,fcntl.LOCK_EX|fcntl.LOCK_NB)
r=subprocess.run(['e2fsck','-fy',str(root)])
assert r.returncode in (0,1),r.returncode
size=4325376*512; offset=1064960*512; chunk=8*1024*1024
with root.open('r+b') as f:
    f.truncate(size+offset)
    pos=size
    while pos:
        start=max(0,pos-chunk); f.seek(start); data=f.read(pos-start)
        assert len(data)==pos-start
        f.seek(start+offset); f.write(data); pos=start
    with lzma.open('build/base.img.xz','rb') as original:
        f.seek(0); remaining=offset
        while remaining:
            data=original.read(min(chunk,remaining)); assert data
            f.write(data); remaining-=len(data)
    f.truncate(4*1024**3); f.flush(); os.fsync(f.fileno())
root.rename(target)
subprocess.run(['fallocate','-d',str(target)],check=True)
# Configure physical I2C through the real firmware config, separate from QEMU DTB.
config=Path('build/boot/config.txt')
subprocess.run(['mcopy','-o','-i',str(target)+'@@8388608','::config.txt',str(config)],check=True)
with config.open('a') as f:f.write('\n[all]\n# rc-pi-lab: external PCA9685 on I2C1\ndtparam=i2c_arm=on\n')
subprocess.run(['mcopy','-o','-i',str(target)+'@@8388608',str(config),'::config.txt'],check=True)
locked.close()
print(target)
