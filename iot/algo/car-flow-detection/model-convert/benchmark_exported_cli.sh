#!/usr/bin/env bash
set -u

MODELS_DIR="./models"
ORT_BIN="${ORT_BIN:-onnxruntime_perf_test}"
MNN_TIMEPROFILE="${MNN_TIMEPROFILE:-timeProfile.out}"
ORT_EP="${ORT_EP:-cpu}"
MNN_FORWARD_TYPE="${MNN_FORWARD_TYPE:-0}"
RUNS="${RUNS:-50}"
OUTPUT_DIR="./outputs/export_benchmark_cli"
MODELS=("yolov8" "yolov12" "yolov13" "yolov13-eucb")

usage() {
  cat <<'EOF'
Benchmark exported ONNX and MNN models without Python bindings.

Usage:
  bash ./model-convert/benchmark_exported_cli.sh [options]

Options:
  --models-dir DIR       Model workspace containing onnx/ and mnn/. Default: ./models
  --ort-bin PATH         Path to onnxruntime_perf_test. Default: onnxruntime_perf_test in PATH
  --mnn-timeprofile PATH Path to MNN timeProfile.out. Default: timeProfile.out in PATH
  --ort-ep NAME          ONNX Runtime EP, e.g. cpu, acl, nnapi, cuda. Default: cpu
  --mnn-forward TYPE     MNN forward type. Common: 0=CPU, 3=OpenCL, 7=Vulkan. Default: 0
  --runs N               Repeat count. Default: 50
  --output-dir DIR       Directory for logs and summary. Default: ./outputs/export_benchmark_cli
  --models LIST          Space separated model names. Default: yolov8 yolov12 yolov13 yolov13-eucb

Examples:
  bash ./model-convert/benchmark_exported_cli.sh \
    --ort-bin /opt/onnxruntime/bin/onnxruntime_perf_test \
    --mnn-timeprofile /opt/MNN/build/timeProfile.out

  ORT_EP=cpu MNN_FORWARD_TYPE=0 RUNS=100 bash ./model-convert/benchmark_exported_cli.sh
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --models-dir)
      MODELS_DIR="$2"
      shift 2
      ;;
    --ort-bin)
      ORT_BIN="$2"
      shift 2
      ;;
    --mnn-timeprofile)
      MNN_TIMEPROFILE="$2"
      shift 2
      ;;
    --ort-ep)
      ORT_EP="$2"
      shift 2
      ;;
    --mnn-forward)
      MNN_FORWARD_TYPE="$2"
      shift 2
      ;;
    --runs)
      RUNS="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --models)
      shift
      MODELS=()
      while [[ $# -gt 0 && "$1" != --* ]]; do
        MODELS+=("$1")
        shift
      done
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[error] unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if ! mkdir -p "$OUTPUT_DIR/logs" 2>/dev/null; then
  echo "[error] cannot create output dir: $OUTPUT_DIR"
  echo "[hint] If it was created by sudo before, run:"
  echo "       sudo chown -R \$(id -u):\$(id -g) $OUTPUT_DIR"
  echo "       or pass --output-dir /tmp/export_benchmark_cli"
  exit 1
fi

if [[ ! -w "$OUTPUT_DIR" || ! -w "$OUTPUT_DIR/logs" ]]; then
  echo "[error] output dir is not writable: $OUTPUT_DIR"
  echo "[hint] If it was created by sudo before, run:"
  echo "       sudo chown -R \$(id -u):\$(id -g) $OUTPUT_DIR"
  echo "       or pass --output-dir /tmp/export_benchmark_cli"
  exit 1
fi

SUMMARY="$OUTPUT_DIR/summary.tsv"

echo -e "model\tbackend\tstatus\tlog" > "$SUMMARY"

if ! command -v "$ORT_BIN" >/dev/null 2>&1 && [[ ! -f "$ORT_BIN" ]]; then
  echo "[warn] onnxruntime_perf_test not found: $ORT_BIN"
  echo "[warn] ONNX tests will be skipped. Set --ort-bin /path/to/onnxruntime_perf_test."
  ORT_BIN=""
elif [[ -n "$ORT_BIN" && ! -x "$ORT_BIN" && -f "$ORT_BIN" ]]; then
  echo "[warn] onnxruntime_perf_test exists but is not executable: $ORT_BIN"
  echo "[warn] ONNX tests will be skipped. Run: chmod +x $ORT_BIN"
  ORT_BIN=""
fi

if ! command -v "$MNN_TIMEPROFILE" >/dev/null 2>&1 && [[ ! -f "$MNN_TIMEPROFILE" ]]; then
  echo "[warn] timeProfile.out not found: $MNN_TIMEPROFILE"
  echo "[warn] MNN tests will be skipped. Set --mnn-timeprofile /path/to/timeProfile.out."
  MNN_TIMEPROFILE=""
elif [[ -n "$MNN_TIMEPROFILE" && ! -x "$MNN_TIMEPROFILE" && -f "$MNN_TIMEPROFILE" ]]; then
  echo "[warn] timeProfile.out exists but is not executable: $MNN_TIMEPROFILE"
  echo "[warn] MNN tests will be skipped. Run: chmod +x $MNN_TIMEPROFILE"
  MNN_TIMEPROFILE=""
fi

echo "[info] models dir: $MODELS_DIR"
echo "[info] output dir: $OUTPUT_DIR"
echo "[info] runs: $RUNS"
echo "[info] onnxruntime ep: $ORT_EP"
echo "[info] mnn forward type: $MNN_FORWARD_TYPE"

for MODEL in "${MODELS[@]}"; do
  ONNX_MODEL="$MODELS_DIR/onnx/$MODEL.onnx"
  MNN_MODEL="$MODELS_DIR/mnn/$MODEL.mnn"

  if [[ -n "$ORT_BIN" ]]; then
    ORT_LOG="$OUTPUT_DIR/logs/${MODEL}_onnx.log"
    if [[ -f "$ONNX_MODEL" ]]; then
      echo
      echo "[onnx] $MODEL"
      echo "[run] $ORT_BIN -e $ORT_EP -r $RUNS $ONNX_MODEL"
      if "$ORT_BIN" -e "$ORT_EP" -r "$RUNS" "$ONNX_MODEL" >"$ORT_LOG" 2>&1; then
        echo "[ok] ONNX log: $ORT_LOG"
        echo -e "$MODEL\tonnx\tok\t$ORT_LOG" >> "$SUMMARY"
      else
        echo "[failed] ONNX log: $ORT_LOG"
        tail -n 30 "$ORT_LOG" || true
        echo -e "$MODEL\tonnx\tfailed\t$ORT_LOG" >> "$SUMMARY"
      fi
    else
      echo "[skip] missing ONNX model: $ONNX_MODEL"
      echo -e "$MODEL\tonnx\tmissing\t$ONNX_MODEL" >> "$SUMMARY"
    fi
  fi

  if [[ -n "$MNN_TIMEPROFILE" ]]; then
    MNN_LOG="$OUTPUT_DIR/logs/${MODEL}_mnn.log"
    if [[ -f "$MNN_MODEL" ]]; then
      echo
      echo "[mnn] $MODEL"
      echo "[run] $MNN_TIMEPROFILE $MNN_MODEL $RUNS $MNN_FORWARD_TYPE"
      if "$MNN_TIMEPROFILE" "$MNN_MODEL" "$RUNS" "$MNN_FORWARD_TYPE" >"$MNN_LOG" 2>&1; then
        echo "[ok] MNN log: $MNN_LOG"
        echo -e "$MODEL\tmnn\tok\t$MNN_LOG" >> "$SUMMARY"
      else
        echo "[failed] MNN log: $MNN_LOG"
        tail -n 30 "$MNN_LOG" || true
        echo -e "$MODEL\tmnn\tfailed\t$MNN_LOG" >> "$SUMMARY"
      fi
    else
      echo "[skip] missing MNN model: $MNN_MODEL"
      echo -e "$MODEL\tmnn\tmissing\t$MNN_MODEL" >> "$SUMMARY"
    fi
  fi
done

echo
echo "[done] summary: $SUMMARY"
cat "$SUMMARY"
