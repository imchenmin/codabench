#!/usr/bin/env bash
set -euo pipefail
case_dir="$1"
out_file="$2"
DIR=$(cd "$(dirname "$0")" && pwd)
JAR="$DIR/gson-2.10.1.jar"
if [ ! -f "$JAR" ]; then
  curl -L -o "$JAR" https://repo1.maven.org/maven2/com/google/code/gson/gson/2.10.1/gson-2.10.1.jar
fi
javac -cp "$JAR" "$DIR/Main.java"
java -cp "$DIR":"$JAR" Main "$case_dir" "$out_file"