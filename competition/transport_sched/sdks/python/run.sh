#!/usr/bin/env bash
set -euo pipefail
case_dir="$1"
out_file="$2"
DIR=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$(dirname "$out_file")"
python3 "$DIR/run.py" --input "$case_dir" --output "$out_file"