#!/bin/sh
# Three independent guest boots, not retries. Stop at the first failure.
set -eu
sha256sum build/rootfs.img > evidence/diagnostic-base-before.sha256
for run in 1 2 3; do
    output="evidence/diagnostic-$run"
    mkdir "$output" # Refuse to overwrite an earlier run.
    status=0
    python3 scripts/run-diagnostic.py > "$output/harness.log" 2>&1 || status=$?
    printf '%s\n' "$status" > "$output/exit.txt"
    for name in boot-stock.log pca-stock.jsonl bridge-test.json; do
        test ! -e "evidence/$name" || cp "evidence/$name" "$output/$name"
    done
    test "$status" = 0 || exit "$status"
    python3 tests/validate_trace.py "$output/pca-stock.jsonl" "$output/boot-stock.log" > "$output/oracle.json"
    sha256sum -c evidence/diagnostic-base-before.sha256 > "$output/base-unchanged.txt"
done
