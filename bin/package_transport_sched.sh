#!/usr/bin/env bash
set -euo pipefail

# Package transport_sched competition artifacts into zips under dist/.
# - Builds per-component zips (ingestion/scoring/datasets/baseline)
# - Builds a standard competition bundle zip (competition.yaml + pages + assets)
# - Builds a full repo folder zip for transport_sched
#
# Usage:
#   bin/package_transport_sched.sh [OUTPUT_DIR]
#
# Example:
#   bin/package_transport_sched.sh            # outputs to ./dist
#   bin/package_transport_sched.sh ./release  # outputs to ./release

OUTPUT_DIR=${1:-dist}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMP_DIR="$ROOT_DIR/competition/transport_sched"

ING_DIR="$COMP_DIR/ingestion_program"
SCORE_DIR="$COMP_DIR/scoring_program"
DATA_DIR="$COMP_DIR/datasets/public"
BASE_DIR="$COMP_DIR/baseline_submission"

SDK_DIR="$COMP_DIR/sdks"
SDK_C_DIR="$SDK_DIR/c"
SDK_CPP_DIR="$SDK_DIR/cpp"
SDK_JAVA_DIR="$SDK_DIR/java"
SDK_PY_DIR="$SDK_DIR/python"

ING_ZIP="$COMP_DIR/ingestion_program.zip"
SCORE_ZIP="$COMP_DIR/scoring_program.zip"
DATA_ZIP="$COMP_DIR/datasets_public.zip"
BASE_ZIP="$COMP_DIR/baseline_submission.zip"

SDK_C_ZIP="$COMP_DIR/sdk_c.zip"
SDK_CPP_ZIP="$COMP_DIR/sdk_cpp.zip"
SDK_JAVA_ZIP="$COMP_DIR/sdk_java.zip"
SDK_PY_ZIP="$COMP_DIR/sdk_python.zip"
SDK_ALL_ZIP="$COMP_DIR/sdks_all.zip"

COMP_BUNDLE_ZIP="$ROOT_DIR/$OUTPUT_DIR/transport_sched_competition_bundle.zip"
FULL_ZIP="$ROOT_DIR/$OUTPUT_DIR/transport_sched_full.zip"

PER_SDK_C_ZIP="$ROOT_DIR/$OUTPUT_DIR/transport_sched_sdk_c.zip"
PER_SDK_CPP_ZIP="$ROOT_DIR/$OUTPUT_DIR/transport_sched_sdk_cpp.zip"
PER_SDK_JAVA_ZIP="$ROOT_DIR/$OUTPUT_DIR/transport_sched_sdk_java.zip"
PER_SDK_PY_ZIP="$ROOT_DIR/$OUTPUT_DIR/transport_sched_sdk_python.zip"
PER_SDK_ALL_ZIP="$ROOT_DIR/$OUTPUT_DIR/transport_sched_sdks.zip"

PER_ING_ZIP="$ROOT_DIR/$OUTPUT_DIR/transport_sched_ingestion_program.zip"
PER_SCORE_ZIP="$ROOT_DIR/$OUTPUT_DIR/transport_sched_scoring_program.zip"
PER_DATA_ZIP="$ROOT_DIR/$OUTPUT_DIR/transport_sched_datasets_public.zip"
PER_BASE_ZIP="$ROOT_DIR/$OUTPUT_DIR/transport_sched_baseline_submission.zip"

command -v zip >/dev/null 2>&1 || { echo "Error: zip is required."; exit 1; }

mkdir -p "$ROOT_DIR/$OUTPUT_DIR"

zip_from_dir() {
  local src_dir="$1"; shift
  local out_zip="$1"; shift
  ( cd "$src_dir" && rm -f "$out_zip" && zip -r -q "$out_zip" . )
}

zip_sdk_dir() {
  local src_dir="$1"; shift
  local out_zip="$1"; shift
  ( cd "$src_dir" && rm -f "$out_zip" && \
    zip -r -q "$out_zip" . \
      -x 'out/*' 'predict' '*.class' )
}

echo "[1/6] Build component zips into competition directory"
zip_from_dir "$ING_DIR" "$ING_ZIP"
zip_from_dir "$SCORE_DIR" "$SCORE_ZIP"
zip_from_dir "$DATA_DIR" "$DATA_ZIP"
zip_from_dir "$BASE_DIR" "$BASE_ZIP"

echo "[2/6] Build SDK zips into competition directory"
zip_sdk_dir "$SDK_C_DIR" "$SDK_C_ZIP"
zip_sdk_dir "$SDK_CPP_DIR" "$SDK_CPP_ZIP"
zip_sdk_dir "$SDK_JAVA_DIR" "$SDK_JAVA_ZIP"
zip_sdk_dir "$SDK_PY_DIR" "$SDK_PY_ZIP"
( cd "$SDK_DIR" && rm -f "$SDK_ALL_ZIP" && \
  zip -r -q "$SDK_ALL_ZIP" . \
    -x '*/out/*' '*/predict' '*.class' )

echo "[3/6] Copy zips to output directory"
cp -f "$ING_ZIP" "$PER_ING_ZIP"
cp -f "$SCORE_ZIP" "$PER_SCORE_ZIP"
cp -f "$DATA_ZIP" "$PER_DATA_ZIP"
cp -f "$BASE_ZIP" "$PER_BASE_ZIP"
cp -f "$SDK_C_ZIP" "$PER_SDK_C_ZIP"
cp -f "$SDK_CPP_ZIP" "$PER_SDK_CPP_ZIP"
cp -f "$SDK_JAVA_ZIP" "$PER_SDK_JAVA_ZIP"
cp -f "$SDK_PY_ZIP" "$PER_SDK_PY_ZIP"
cp -f "$SDK_ALL_ZIP" "$PER_SDK_ALL_ZIP"

echo "[4/6] Build standard competition bundle zip (competition.yaml at root)"
rm -f "$COMP_BUNDLE_ZIP"
( cd "$COMP_DIR" && \
  zip -r -q "$COMP_BUNDLE_ZIP" \
    competition.yaml \
    overview.md \
    evaluation.md \
    data.md \
    terms.md \
    images/logo.png \
    "$(basename "$ING_ZIP")" \
    "$(basename "$SCORE_ZIP")" \
    "$(basename "$DATA_ZIP")" \
    "$(basename "$BASE_ZIP")" \
    "$(basename "$SDK_ALL_ZIP")" \
)

echo "[5/6] Build full folder zip"
rm -f "$FULL_ZIP"
zip -r -q "$FULL_ZIP" "$COMP_DIR"

echo "[6/6] Done"
echo "Artifacts:"
echo "  - $PER_ING_ZIP"
echo "  - $PER_SCORE_ZIP"
echo "  - $PER_DATA_ZIP"
echo "  - $PER_BASE_ZIP"
echo "  - $PER_SDK_C_ZIP"
echo "  - $PER_SDK_CPP_ZIP"
echo "  - $PER_SDK_JAVA_ZIP"
echo "  - $PER_SDK_PY_ZIP"
echo "  - $PER_SDK_ALL_ZIP"
echo "  - $COMP_BUNDLE_ZIP"
echo "  - $FULL_ZIP"
