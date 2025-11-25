#!/usr/bin/env bash
set -euo pipefail
case_dir="$1"
out_file="$2"
DIR=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$DIR/vendor"
mkdir -p "$(dirname "$out_file")"
if [ ! -f "$DIR/vendor/cJSON.c" ] || [ ! -f "$DIR/vendor/cJSON.h" ]; then
  curl -L -o "$DIR/vendor/cJSON.c" https://raw.githubusercontent.com/DaveGamble/cJSON/master/cJSON.c
  curl -L -o "$DIR/vendor/cJSON.h" https://raw.githubusercontent.com/DaveGamble/cJSON/master/cJSON.h
fi
gcc -O2 -pipe "$DIR/main.c" "$DIR/vendor/cJSON.c" -I"$DIR/vendor" -o "$DIR/predict"
"$DIR/predict" "$case_dir" "$out_file"