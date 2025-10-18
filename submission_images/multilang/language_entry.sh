#!/bin/bash
set -euo pipefail

shopt -s globstar nullglob

PROGRAM_DIR=${PROGRAM_DIR:-/app/program}
OUTPUT_DIR=${OUTPUT_DIR:-/app/output}
BUILD_DIR="${PROGRAM_DIR}/build"

mkdir -p "${BUILD_DIR}" "${OUTPUT_DIR}"

LANGUAGE=${LANGUAGE:-auto}
if [[ "${LANGUAGE}" == "auto" ]]; then
    if compgen -G "${PROGRAM_DIR}/**/*.cpp" > /dev/null || compgen -G "${PROGRAM_DIR}/*.cpp" > /dev/null; then
        LANGUAGE="cpp"
    elif compgen -G "${PROGRAM_DIR}/**/*.c" > /dev/null || compgen -G "${PROGRAM_DIR}/*.c" > /dev/null; then
        LANGUAGE="c"
    elif compgen -G "${PROGRAM_DIR}/**/*.java" > /dev/null || compgen -G "${PROGRAM_DIR}/*.java" > /dev/null; then
        LANGUAGE="java"
    elif compgen -G "${PROGRAM_DIR}/**/*.py" > /dev/null || compgen -G "${PROGRAM_DIR}/*.py" > /dev/null; then
        LANGUAGE="python"
    else
        echo "Unable to detect language in ${PROGRAM_DIR}" >&2
        exit 1
    fi
fi

echo "Detected language: ${LANGUAGE}"

case "${LANGUAGE}" in
    c)
        mapfile -t SRC < <(find "${PROGRAM_DIR}" -name '*.c')
        [[ ${#SRC[@]} -gt 0 ]] || { echo "No C sources found" >&2; exit 1; }
        gcc -O2 -std=c17 "${SRC[@]}" -o "${BUILD_DIR}/app"
        "${BUILD_DIR}/app"
        ;;
    cpp)
        mapfile -t SRC < <(find "${PROGRAM_DIR}" -name '*.cpp')
        [[ ${#SRC[@]} -gt 0 ]] || { echo "No C++ sources found" >&2; exit 1; }
        g++ -O2 -std=c++17 "${SRC[@]}" -o "${BUILD_DIR}/app"
        "${BUILD_DIR}/app"
        ;;
    java)
        mapfile -t SRC < <(find "${PROGRAM_DIR}" -name '*.java')
        [[ ${#SRC[@]} -gt 0 ]] || { echo "No Java sources found" >&2; exit 1; }
        javac -d "${BUILD_DIR}" "${SRC[@]}"
        pushd "${BUILD_DIR}" >/dev/null
        java ${JAVA_OPTS:-} ${MAIN_CLASS:-Main}
        popd >/dev/null
        ;;
    python)
        PYTHON_ENTRY=${PYTHON_ENTRY:-main.py}
        if [[ -f "${PROGRAM_DIR}/${PYTHON_ENTRY}" ]]; then
            python3 "${PROGRAM_DIR}/${PYTHON_ENTRY}"
        else
            echo "Python entry ${PYTHON_ENTRY} not found" >&2
            exit 1
        fi
        ;;
    *)
        echo "Unsupported language: ${LANGUAGE}" >&2
        exit 1
        ;;
esac
