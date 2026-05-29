# RTMP Service Auto Start

This directory provides the RTMP push startup script and the matching
`systemd` unit template for Ubuntu or Phytium Pi deployments:

- `iot/start_sh/start_rtmp_service.sh`
- `iot/start_sh/rtmp-push.service`

The startup path now defaults to `ffmpeg` because it has been more stable
than the Python/OpenCV pipeline on the Phytium Pi camera path.

## Default behavior

The startup script uses:

- `PUSH_BACKEND=ffmpeg` by default
- software MJPEG decode via `-c:v mjpeg`
- `libx264 + ultrafast + zerolatency`
- a balanced default profile: `960x540`, `25fps`, `1500k`
- automatic ffmpeg restart when the stream process exits
- RTMP output to `rtmp://123.56.248.17:1935/live/raw`

You can still fall back to the old Python pipeline with:

```bash
PUSH_BACKEND=python /bin/bash /home/user/Documents/iot/start_sh/start_rtmp_service.sh
```

## Recommended ffmpeg parameters

These are the default tuning values used by the startup script:

```bash
CAMERA_SOURCE=/dev/video0
FFMPEG_INPUT_FORMAT=mjpeg
FFMPEG_CAMERA_FRAMERATE=25
FFMPEG_CAMERA_VIDEO_SIZE=1280x720
FFMPEG_FILTER=fps=25,scale=960:540
FFMPEG_BITRATE=1500k
FFMPEG_MAXRATE=1500k
FFMPEG_BUFSIZE=750k
FFMPEG_GOP=25
FFMPEG_RESTART_DELAY=3
RTMP_URL=rtmp://123.56.248.17:1935/live/raw
```

This corresponds to the manual validation command:

```bash
ffmpeg -hide_banner \
  -f v4l2 \
  -thread_queue_size 64 \
  -input_format mjpeg \
  -framerate 25 \
  -video_size 1280x720 \
  -c:v mjpeg \
  -i /dev/video0 \
  -vf "fps=25,scale=960:540" \
  -an \
  -c:v libx264 \
  -preset ultrafast \
  -tune zerolatency \
  -pix_fmt yuv420p \
  -b:v 1500k \
  -maxrate 1500k \
  -bufsize 750k \
  -g 25 \
  -bf 0 \
  -f flv \
  rtmp://123.56.248.17:1935/live/raw
```

## 1. Make the startup script executable

```bash
chmod +x /home/user/Documents/iot/start_sh/start_rtmp_service.sh
```

## 2. Test the startup script manually

```bash
/bin/bash /home/user/Documents/iot/start_sh/start_rtmp_service.sh
```

Logs:

```bash
tail -f /home/user/Documents/iot/rtmpService/logs/rtmp_push.log
```

## 3. Install the systemd service

```bash
sudo cp /home/user/Documents/iot/start_sh/rtmp-push.service /etc/systemd/system/rtmp-push.service
sudo systemctl daemon-reload
sudo systemctl enable rtmp-push.service
sudo systemctl start rtmp-push.service
```

## 4. Recommended service environment

Confirm the service file matches your real deployment path and includes a
usable ffmpeg binary:

```ini
[Service]
WorkingDirectory=/home/user/Documents/iot/rtmpService
ExecStart=/bin/bash /home/user/Documents/iot/start_sh/start_rtmp_service.sh
User=user
Environment=PUSH_BACKEND=ffmpeg
Environment=FFMPEG_BIN=ffmpeg
Environment=CAMERA_SOURCE=/dev/video0
Environment=RTMP_URL=rtmp://123.56.248.17:1935/live/raw
Environment=FFMPEG_CAMERA_FRAMERATE=25
Environment=FFMPEG_CAMERA_VIDEO_SIZE=1280x720
Environment=FFMPEG_FILTER=fps=25,scale=960:540
Environment=FFMPEG_BITRATE=1500k
Environment=FFMPEG_MAXRATE=1500k
Environment=FFMPEG_BUFSIZE=750k
Environment=FFMPEG_GOP=25
Environment=FFMPEG_RESTART_DELAY=3
```

If you need to return to the Python path, add:

```ini
Environment=PUSH_BACKEND=python
Environment=PYTHON_BIN=python3
```

## 5. Check service status

```bash
systemctl status rtmp-push.service -l
journalctl -u rtmp-push.service -f
tail -f /home/user/Documents/iot/rtmpService/logs/rtmp_push.log
```

## 6. Troubleshooting

If the page only shows the first image and keeps spinning, verify whether the
publisher is still running when the browser connects. In SRS logs:

- `publish timeout 5000ms` means the publisher stopped sending data
- `writev timeout 30000 ms` in `do_playing()` means the playback client was too
  slow or stalled

For end-to-end validation, prefer `ffplay` over VLC:

```bash
ffplay -fflags nobuffer -flags low_delay -probesize 32 -analyzeduration 0 \
  rtmp://123.56.248.17:1935/live/raw
```

```bash
ffplay -fflags nobuffer -flags low_delay -probesize 32 -analyzeduration 0 \
  http://123.56.248.17:8080/live/raw.flv
```
