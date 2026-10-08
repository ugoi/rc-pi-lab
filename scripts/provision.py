#!/usr/bin/env python3
"""Offline guest provisioning, no mount, binfmt or host changes required."""
from pathlib import Path
import subprocess,zipfile,hashlib
b=Path('build'); q=b/'packages';q.mkdir(exist_ok=True)
# pip validates both versions and hashes; host Python version cannot change ABI.
subprocess.run(['python3','-m','venv',str(b/'pkgtools')],check=True)
subprocess.run([str(b/'pkgtools/bin/pip'),'download','--require-hashes','--only-binary=:all:',
 '--platform','manylinux2014_aarch64','--python-version','311',
 '--dest',str(b/'wheels'),'-r','guest/requirements.lock'],check=True)
for w in sorted((b/'wheels').glob('*.whl')):
    with zipfile.ZipFile(w) as z:z.extractall(q)
cmd=['mkdir /opt/rc-lab','mkdir /opt/rc-lab/packages']
for f in sorted(q.rglob('*'),key=lambda p:(len(p.parts),str(p))):
    dest='/opt/rc-lab/packages/'+f.relative_to(q).as_posix()
    cmd.append('mkdir '+dest if f.is_dir() else f'write {f.resolve()} {dest}')
for name in ('app.py','probe.py','verify_packages.py','run.sh'):
    cmd.append(f'write {Path("guest",name).resolve()} /opt/rc-lab/{name}')
cmd += [f'write {Path("guest/rc-init").resolve()} /rc-init',
 'set_inode_field /rc-init mode 0100755',
 f'write {Path("guest/rc-lab.service").resolve()} /etc/systemd/system/rc-lab.service',
 'symlink /etc/systemd/system/multi-user.target.wants/rc-lab.service /etc/systemd/system/rc-lab.service']
(b/'inject.debugfs').write_text('\n'.join(cmd)+'\n')
subprocess.run(['debugfs','-w','-f',str(b/'inject.debugfs'),str(b/'rootfs.img')],check=True)
# debugfs may exit 0 on command errors: verify each application byte by readback.
for name in ('app.py','probe.py','verify_packages.py','run.sh'):
    out=b/('verify-'+name)
    subprocess.run(['debugfs','-R',f'dump /opt/rc-lab/{name} {out}',str(b/'rootfs.img')],check=True)
    assert out.read_bytes()==Path('guest',name).read_bytes(),name
    out.unlink()
