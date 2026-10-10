#!/bin/sh
set -eu
cd /work
sh m3/boot.sh >> evidence/m3/qemu.log 2>&1 &
qemu_pid=$!
python3 m3/bridge.py >> evidence/m3/bridge-console.log 2>&1 &
bridge_pid=$!
trap 'kill "$bridge_pid" "$qemu_pid" 2>/dev/null || true; wait' INT TERM EXIT
wait "$qemu_pid"
