#!/bin/bash
set -euo pipefail

OUTPUT_DIR=${OUTPUT_DIR:-/app/output}
mkdir -p build "${OUTPUT_DIR}"

javac -d build src/Main.java
pushd build >/dev/null
java Main "${OUTPUT_DIR}/results.txt"
popd >/dev/null
