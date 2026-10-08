#!/bin/sh
set -eu
mkdir -p build evidence
cc -std=c11 -Wall -Wextra -Werror tests/core.c -o build/test-core
build/test-core | tee evidence/core-test.log
