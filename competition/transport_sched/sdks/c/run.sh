#!/usr/bin/env bash
set -euo pipefail
case_dir="$1"
out_file="$2"
gcc -O2 -pipe main.c -o predict
./predict "$case_dir" "$out_file"