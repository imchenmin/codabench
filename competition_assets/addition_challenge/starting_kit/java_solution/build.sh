#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build"
DEFAULT_INPUT="${SCRIPT_DIR}/data/inputs.csv"
DEFAULT_OUTPUT="${SCRIPT_DIR}/output/predictions.csv"

INPUT_PATH="${1:-${INPUT_CSV:-${DEFAULT_INPUT}}}"
OUTPUT_PATH="${2:-${OUTPUT_CSV:-${DEFAULT_OUTPUT}}}"

mkdir -p "${BUILD_DIR}"
mkdir -p "$(dirname "${OUTPUT_PATH}")"

javac -d "${BUILD_DIR}" "${SCRIPT_DIR}/src/Main.java"
pushd "${BUILD_DIR}" >/dev/null
java Main "${INPUT_PATH}" "${OUTPUT_PATH}"
popd >/dev/null

echo "预测结果已写入 ${OUTPUT_PATH}"
