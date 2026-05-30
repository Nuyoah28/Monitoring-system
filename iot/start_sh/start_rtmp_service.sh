#!/usr/bin/env bash
set -u

RTMP_URL="${RTMP_URL:-rtmp://123.56.248.17:1935/live/raw}"
VIDEO_DEVICE="${VIDEO_DEVICE:-/dev/video0}"
LOG_DIR="${LOG_DIR:-/home/user/Documents/iot/rtmpService/logs}"
LOG_FILE="${LOG_FILE:-$LOG_DIR/rtmp_push.log}"

INPUT_SIZE="${INPUT_SIZE:-1280x720}"
INPUT_FPS="${INPUT_FPS:-30}"
OUTPUT_SIZE="${OUTPUT_SIZE:-960:540}"
OUTPUT_FPS="${OUTPUT_FPS:-25}"
VIDEO_BITRATE="${VIDEO_BITRATE:-2500k}"
VIDEO_MAXRATE="${VIDEO_MAXRATE:-3000k}"
VIDEO_BUFSIZE="${VIDEO_BUFSIZE:-1500k}"
GOP="${GOP:-25}"
RESTART_DELAY="${RESTART_DELAY:-2}"

FFMPEG_BIN="${FFMPEG_BIN:-/usr/local/bin/ffmpeg}"
if [ ! -x "$FFMPEG_BIN" ]; then
  FFMPEG_BIN="$(command -v ffmpeg || true)"
fi

mkdir -p "$LOG_DIR"

if [ -z "$FFMPEG_BIN" ]; then
  echo "$(date '+%F %T') ERROR: ffmpeg not found" >> "$LOG_FILE"
  exit 127
fi

echo "$(date '+%F %T') RTMP push service starting, url=$RTMP_URL" >> "$LOG_FILE"

while true; do
  echo "$(date '+%F %T') Starting ffmpeg push..." >> "$LOG_FILE"

  "$FFMPEG_BIN" \
    -hide_banner \
    -loglevel info \
    -fflags +genpts+discardcorrupt \
    -f v4l2 \
    -thread_queue_size 64 \
    -input_format mjpeg \
    -framerate "$INPUT_FPS" \
    -video_size "$INPUT_SIZE" \
    -err_detect ignore_err \
    -i "$VIDEO_DEVICE" \
    -vf "fps=${OUTPUT_FPS},scale=${OUTPUT_SIZE}" \
    -r "$OUTPUT_FPS" \
    -an \
    -c:v libx264 \
    -preset ultrafast \
    -tune zerolatency \
    -pix_fmt yuv420p \
    -b:v "$VIDEO_BITRATE" \
    -maxrate "$VIDEO_MAXRATE" \
    -bufsize "$VIDEO_BUFSIZE" \
    -g "$GOP" \
    -keyint_min "$GOP" \
    -sc_threshold 0 \
    -bf 0 \
    -x264-params "keyint=${GOP}:min-keyint=${GOP}:scenecut=0:repeat-headers=1" \
    -flvflags no_duration_filesize \
    -f flv "$RTMP_URL" >> "$LOG_FILE" 2>&1

  status=$?
  echo "$(date '+%F %T') ffmpeg exited with code $status, restart in ${RESTART_DELAY}s" >> "$LOG_FILE"
  sleep "$RESTART_DELAY"
done
