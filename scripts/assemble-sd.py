#!/usr/bin/env python3
"""Convert the tested task-owned rootfs to a full SD image in place to limit disk use.
This destroys ONLY that intermediate rootfs; original compressed image is retained.
Run only with QEMU stopped. Needs ~1 GiB additional free disk space.
"""
import lzma,os
from pathlib import Path
root=Path('build/rootfs.img'); target=Path('build/rc-pi3.img')
assert root.exists() and not target.exists()
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
print(target)
