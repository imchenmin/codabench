#!/bin/bash
set -euo pipefail

OUTPUT_DIR=${OUTPUT_DIR:-/app/output}
mkdir -p build "${OUTPUT_DIR}"

g++ -O2 -std=c++17 src/main.cpp -o build/app
./build/app "${OUTPUT_DIR}/results.txt"
