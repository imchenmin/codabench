#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/output"
mkdir -p "${SCRIPT_DIR}/build" "${OUTPUT_DIR}"

javac -d "${SCRIPT_DIR}/build" "${SCRIPT_DIR}/src/Main.java"
pushd "${SCRIPT_DIR}/build" >/dev/null
java Main "${SCRIPT_DIR}/data/inputs.csv" "${OUTPUT_DIR}/predictions.csv"
popd >/dev/null

echo "预测结果已写入 ${OUTPUT_DIR}/predictions.csv"
