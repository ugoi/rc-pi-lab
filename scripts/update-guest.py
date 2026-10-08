#!/usr/bin/env python3
"""Refresh only lab files in an OFFLINE, existing diagnostic rootfs."""
import subprocess
from pathlib import Path
b=Path('build');disk=b/'rootfs.img'
# Replaying the journal after debugfs edits could otherwise undo those edits.
r=subprocess.run(['e2fsck','-fy',str(disk)])
assert r.returncode in (0,1),r.returncode
files={f'/opt/rc-lab/{n}':Path('guest',n) for n in ('app.py','probe.py','verify_packages.py','run.sh')}
files['/opt/rc-lab/device-matrix.py']=Path('scripts/device-matrix.py')
files['/rc-init']=Path('guest/rc-init')
files['/etc/systemd/system/rc-lab.service']=Path('guest/rc-lab.service')
commands=[]
for dest,source in files.items():commands.extend([f'rm {dest}',f'write {source.resolve()} {dest}'])
commands.append('set_inode_field /rc-init mode 0100755')
(b/'update.debugfs').write_text('\n'.join(commands)+'\n')
subprocess.run(['debugfs','-w','-f',str(b/'update.debugfs'),str(disk)],check=True)
for dest,source in files.items():
    out=b/'update-readback'
    subprocess.run(['debugfs','-R',f'dump {dest} {out}',str(disk)],check=True)
    assert out.read_bytes()==source.read_bytes(),dest
    out.unlink()
print('Guest application and harness files verified byte-for-byte')
