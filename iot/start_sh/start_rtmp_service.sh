#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
RTMP_DIR="$IOT_DIR/rtmpService"
PYTHON_SCRIPT="$RTMP_DIR/push.py"

PYTHON_BIN="${PYTHON_BIN:-python3}"
LOG_DIR="${LOG_DIR:-$RTMP_DIR/logs}"
LOG_FILE="${LOG_FILE:-$LOG_DIR/rtmp_push.log}"

log() {
  printf '[rtmp-start] %s\n' "$1"
}

require_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    log "Command not found: $cmd"
    exit 1
  fi
}

prepare_environment() {
  require_command "$PYTHON_BIN"

  if [ ! -f "$PYTHON_SCRIPT" ]; then
    log "Python script not found: $PYTHON_SCRIPT"
    exit 1
  fi

  mkdir -p "$LOG_DIR"
}

main() {
  prepare_environment
  cd "$RTMP_DIR"

  log "Starting RTMP push service"
  log "Python: $PYTHON_BIN"
  log "Script: $PYTHON_SCRIPT"
  log "Log: $LOG_FILE"

  exec "$PYTHON_BIN" -u "$PYTHON_SCRIPT" >>"$LOG_FILE" 2>&1
}

main "$@"
