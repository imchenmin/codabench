#!/usr/bin/env bash
set -euo pipefail
case_dir="$1"
out_file="$2"
g++ -std=c++17 -O2 main.cpp -o predict
./predict "$case_dir" "$out_file"