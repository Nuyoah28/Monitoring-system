# RTMP Push Usage

这个目录里的 `push.py` 用于从本地摄像头采集画面，并持续推送到 RTMP 服务端。

这版脚本重点偏向“直播实时性优先”：

- 摄像头线程持续读取最新帧，旧帧会被覆盖，不再尽量补发历史帧
- 主推流线程按目标帧率发送，避免卡住几秒后再快速追帧
- 适合飞腾派这类 CPU 和网络都比较紧张的设备

## 特性

- 摄像头打开失败时自动重试
- 摄像头读帧连续失败时自动释放并重连
- RTMP 服务端断开时自动重连
- 适合无桌面的 Linux 环境，不再调用 `cv2.destroyAllWindows()`
- 周期性输出心跳日志，便于判断服务是否持续工作
- 使用“最新帧覆盖”策略，减少卡顿后快进追帧
- 支持限制编码码率、GOP 和 B 帧数量，降低大幅运动时的抖动

## 配置方式

脚本默认读取环境变量；没有设置时会使用内置默认值。

| 变量名 | 默认值 | 说明 |
| --- | --- | --- |
| `RTMP_URL` | `rtmp://123.56.248.17:1935/live/raw` | RTMP 推流地址 |
| `CAMERA_SOURCE` | 空 | 摄像头源，支持 `/dev/video0` 或数字字符串 |
| `CAMERA_INDEX` | `1` | 当 `CAMERA_SOURCE` 未设置时使用的索引 |
| `FRAME_WIDTH` | `1280` | 采集宽度 |
| `FRAME_HEIGHT` | `720` | 采集高度 |
| `FRAME_RATE` | `15` | 目标帧率 |
| `OPEN_RETRY_DELAY` | `2` | 打开摄像头或 RTMP 重试间隔，单位秒 |
| `READ_RETRY_DELAY` | `0.05` | 单次读帧失败后的等待时间，单位秒 |
| `READ_FAILURE_THRESHOLD` | `3` | 连续读帧失败多少次后重连摄像头 |
| `HEARTBEAT_INTERVAL` | `30` | 心跳日志间隔，单位秒；设为 `0` 可关闭 |
| `BIT_RATE` | `1200000` | 目标编码码率，单位 bit/s |
| `MAX_RATE` | 与 `BIT_RATE` 相同 | 编码最大码率，单位 bit/s |
| `ENCODER_BUFFER_SIZE` | `BIT_RATE * 2` | 编码缓冲大小，单位 bit/s |
| `GOP_SIZE` | `max(15, FRAME_RATE)` | 关键帧间隔 |
| `MAX_B_FRAMES` | `0` | B 帧数量，直播建议保持 `0` |
| `CRF` | `28` | x264 质量参数，数值越大越省带宽 |
| `ENCODER_PRESET` | `ultrafast` | x264 预设 |
| `NO_NEW_FRAME_DELAY` | `0.005` | 没有新帧可发时的等待时间，单位秒 |

## 手动运行

```bash
cd /home/user/Documents/iot/rtmpService
python3 -u push.py
```

如果摄像头编号不稳定，推荐显式指定设备节点：

```bash
CAMERA_SOURCE=/dev/video0 python3 -u push.py
```

如果飞腾派推 720p 仍然偶发卡顿，建议先用这组更稳的参数：

```bash
CAMERA_SOURCE=/dev/video0 \
FRAME_WIDTH=960 \
FRAME_HEIGHT=540 \
FRAME_RATE=12 \
BIT_RATE=800000 \
MAX_RATE=800000 \
CRF=30 \
python3 -u push.py
```

如果还不稳，再降到：

```bash
CAMERA_SOURCE=/dev/video0 \
FRAME_WIDTH=640 \
FRAME_HEIGHT=360 \
FRAME_RATE=10 \
BIT_RATE=500000 \
MAX_RATE=500000 \
CRF=32 \
python3 -u push.py
```

## systemd 示例

如果你通过 `systemd` 启动，建议在 service 里增加环境变量，避免 USB 摄像头重枚举后索引变化：

```ini
[Service]
Environment=PYTHON_BIN=python3
Environment=CAMERA_SOURCE=/dev/video0
Environment=RTMP_URL=rtmp://123.56.248.17:1935/live/raw
Environment=FRAME_WIDTH=960
Environment=FRAME_HEIGHT=540
Environment=FRAME_RATE=12
Environment=BIT_RATE=800000
Environment=MAX_RATE=800000
Environment=CRF=30
ExecStart=/bin/bash /home/user/Documents/iot/start_sh/start_rtmp_service.sh
```

修改后执行：

```bash
sudo systemctl daemon-reload
sudo systemctl restart rtmp-push.service
```

## 查看日志

```bash
systemctl status rtmp-push.service -l
journalctl -u rtmp-push.service -f
tail -f /home/user/Documents/iot/rtmpService/logs/rtmp_push.log
```

## 如何判断是不是“追帧卡顿”

如果你看到的现象是：

- 画面突然停住 2 到 3 秒
- 随后在很短时间内把刚才那段画面快速播放完

这通常不是纯断流，而是缓冲区里积压了旧帧。

新脚本会优先丢弃旧帧、只推最新帧，所以正常现象应该更接近：

- 画面偶尔轻微跳帧
- 但不会长时间冻结后再明显快进

如果还是经常出现，通常说明飞腾派的 CPU 编码能力或上行带宽仍然不够，需要继续降低：

- `FRAME_RATE`
- `FRAME_WIDTH` / `FRAME_HEIGHT`
- `BIT_RATE`

## 排查摄像头

如果日志里出现 `can't open camera by index`、`select() timeout`、`No such device`，优先检查摄像头设备：

```bash
ls -l /dev/video*
v4l2-ctl --list-devices
v4l2-ctl --all -d /dev/video0
lsusb
dmesg -Tw | grep -Ei "usb|uvc|video|reset|disconnect"
```

## 部署提醒

你当前飞腾派实际运行的文件路径是 `/home/user/Documents/iot/rtmpService/push.py`。如果仓库目录和部署目录不是同一个位置，请把本目录下更新后的 `push.py` 和本说明同步到飞腾派实际部署路径，再重启服务验证。
