"""Create a separate M3 rootfs; never modify M1/M2 image or packages."""

import subprocess, os
from pathlib import Path

src = Path(os.environ.get("M3_BASE_IMAGE", "build/qa-fixes-work/build/rootfs.img"))
dst = Path("build/m3/rootfs.img")
if dst.exists():
    raise SystemExit(
        "Refusing to overwrite M3 image; stop runtime and remove only this derived image explicitly"
    )
subprocess.run(
    ["cp", "--reflink=auto", "--sparse=always", str(src), str(dst)], check=True
)
r = subprocess.run(["e2fsck", "-fy", str(dst)], check=False)
assert r.returncode in (0, 1)
commands = []
for source, target in [
    ("m3/init", "/m3-init"),
    ("m3/guest_control.py", "/opt/rc-lab/guest_control.py"),
]:
    commands += [
        f"write /work/{source} {target}",
        f"set_inode_field {target} mode 0100755",
    ]
Path("build/m3/inject").write_text("\n".join(commands) + "\n")
subprocess.run(["debugfs", "-w", "-f", "build/m3/inject", str(dst)], check=True)
for source, target in [
    ("m3/init", "/m3-init"),
    ("m3/guest_control.py", "/opt/rc-lab/guest_control.py"),
]:
    out = Path("build/m3/readback")
    out.unlink(missing_ok=True)
    subprocess.run(["debugfs", "-R", f"dump {target} {out}", str(dst)], check=True)
    assert out.read_bytes() == Path(source).read_bytes()
print("M3_GUEST_FILES_BYTE_EQUAL")
