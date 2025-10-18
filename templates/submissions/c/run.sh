#!/bin/bash
set -euo pipefail

OUTPUT_DIR=${OUTPUT_DIR:-/app/output}
mkdir -p build "${OUTPUT_DIR}"

gcc -O2 -std=c17 src/main.c -o build/app
./build/app "${OUTPUT_DIR}/results.txt"
