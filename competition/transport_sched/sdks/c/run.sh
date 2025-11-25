#!/usr/bin/env bash
set -euo pipefail
case_dir="$1"
out_file="$2"
DIR=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$DIR/vendor"
mkdir -p "$(dirname "$out_file")"

# 下载依赖（cJSON）
if [ ! -f "$DIR/vendor/cJSON.c" ] || [ ! -f "$DIR/vendor/cJSON.h" ]; then
  curl -L -o "$DIR/vendor/cJSON.c" https://raw.githubusercontent.com/DaveGamble/cJSON/master/cJSON.c
  curl -L -o "$DIR/vendor/cJSON.h" https://raw.githubusercontent.com/DaveGamble/cJSON/master/cJSON.h
fi

# 检测二进制是否为 ELF（Linux 可运行）
is_elf=false
if [ -f "$DIR/predict" ]; then
  if head -c 4 "$DIR/predict" | od -An -t x1 | tr -d ' \n' | grep -qi '^7f454c46'; then
    is_elf=true
  fi
fi

if [ "$is_elf" = true ]; then
  "$DIR/predict" "$case_dir" "$out_file"
  exit 0
fi

# 若无可运行的 ELF 二进制，则尝试编译；若环境缺 gcc 则给出明确错误
if command -v gcc >/dev/null 2>&1; then
  gcc -O2 -pipe "$DIR/main.c" "$DIR/vendor/cJSON.c" -I"$DIR/vendor" -o "$DIR/predict"
  "$DIR/predict" "$case_dir" "$out_file"
else
  echo "ERROR: gcc not found in runtime. Please include prebuilt Linux amd64 ELF binary 'predict' in submission." >&2
  echo "Hint: build inside a Linux container or use cross-compiler to produce an ELF binary." >&2
  exit 127
fi
