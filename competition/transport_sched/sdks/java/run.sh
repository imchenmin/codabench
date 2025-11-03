#!/usr/bin/env bash
set -euo pipefail
case_dir="$1"
out_file="$2"
javac Main.java
java Main "$case_dir" "$out_file"