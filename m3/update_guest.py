"""Refresh only the M3 app/init offline. QEMU in this container must be stopped."""

from pathlib import Path
import subprocess

for p in Path("/proc").glob("[0-9]*/comm"):
    try:
        if p.read_text().strip().startswith("qemu-system"):
            raise SystemExit("Stop QEMU before offline update")
    except FileNotFoundError:
        pass
commands = []
for source, target in [
    ("m3/init", "/m3-init"),
    ("m3/guest_control.py", "/opt/rc-lab/guest_control.py"),
]:
    commands += [
        f"rm {target}",
        f"write /work/{source} {target}",
        f"set_inode_field {target} mode 0100755",
    ]
Path("build/m3/update").write_text("\n".join(commands) + "\n")
subprocess.run(
    ["debugfs", "-w", "-f", "build/m3/update", "build/m3/rootfs.img"], check=True
)
for source, target in [
    ("m3/init", "/m3-init"),
    ("m3/guest_control.py", "/opt/rc-lab/guest_control.py"),
]:
    out = Path("build/m3/readback")
    out.unlink(missing_ok=True)
    subprocess.run(
        ["debugfs", "-R", f"dump {target} {out}", "build/m3/rootfs.img"], check=True
    )
    assert out.read_bytes() == Path(source).read_bytes()
print("M3_GUEST_FILES_BYTE_EQUAL")
