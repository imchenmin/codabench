#!/usr/bin/env bash
set -euo pipefail
case_dir="$1"
out_file="$2"
DIR=$(cd "$(dirname "$0")" && pwd)
if [ ! -f "$DIR/json.hpp" ]; then
  curl -L -o "$DIR/json.hpp" https://raw.githubusercontent.com/nlohmann/json/master/single_include/nlohmann/json.hpp
fi
g++ -std=c++17 -O2 "$DIR/main.cpp" -o "$DIR/predict"
mkdir -p "$(dirname "$out_file")"
"$DIR/predict" "$case_dir" "$out_file"