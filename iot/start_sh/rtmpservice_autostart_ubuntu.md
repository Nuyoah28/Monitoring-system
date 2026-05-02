# RTMP Service Auto Start

这个目录提供 RTMP 推流服务的开机自启脚本和 `systemd` 模板:

- [start_rtmp_service.sh](/d:/桌面/新建文件夹/Monitoring-system/iot/start_sh/start_rtmp_service.sh)
- [rtmp-push.service](/d:/桌面/新建文件夹/Monitoring-system/iot/start_sh/rtmp-push.service)

它们用于在 Ubuntu 或飞腾派上开机自动启动:

- `iot/rtmpService/push.py`

## 功能说明

- 启动前自动检查 `python3`
- 自动切换到 `iot/rtmpService` 目录运行
- 把推流日志写到 `iot/rtmpService/logs/rtmp_push.log`
- 如果进程异常退出，`systemd` 会自动重启

## 1. 先确认 Python 环境

手动测试:

```bash
cd /home/user/Documents/iot/rtmpService
python3 push.py
```

如果这里都跑不起来，先安装依赖，例如:

```bash
pip3 install opencv-python av
```

如果你使用虚拟环境，也可以，后面只要把 `PYTHON_BIN` 改成虚拟环境里的 Python 绝对路径即可。

## 2. 给启动脚本执行权限

```bash
chmod +x /home/user/Documents/iot/start_sh/start_rtmp_service.sh
```

## 3. 先手动测试启动脚本

```bash
/bin/bash /home/user/Documents/iot/start_sh/start_rtmp_service.sh
```

日志查看:

```bash
tail -f /home/user/Documents/iot/rtmpService/logs/rtmp_push.log
```

## 4. 配置 systemd 服务

先复制模板:

```bash
sudo cp /home/user/Documents/iot/start_sh/rtmp-push.service /etc/systemd/system/rtmp-push.service
```

然后按你的实际路径修改:

```bash
sudo nano /etc/systemd/system/rtmp-push.service
```

至少检查这几项:

```ini
WorkingDirectory=/home/user/Documents/iot/rtmpService
ExecStart=/bin/bash /home/user/Documents/iot/start_sh/start_rtmp_service.sh
User=user
Environment=PYTHON_BIN=python3
```

如果你的项目不在 `/home/user/Documents/iot`，要改成你自己的绝对路径。

如果你用虚拟环境，例如:

```ini
Environment=PYTHON_BIN=/home/user/miniconda3/envs/iot/bin/python
```

## 5. 启用开机自启

```bash
sudo systemctl daemon-reload
sudo systemctl enable rtmp-push.service
sudo systemctl start rtmp-push.service
```

## 6. 查看运行状态

```bash
systemctl status rtmp-push.service
sudo journalctl -u rtmp-push.service -b
tail -f /home/user/Documents/iot/rtmpService/logs/rtmp_push.log
```

## 7. 常见问题

### 1. 服务启动失败

先看:

```bash
systemctl status rtmp-push.service -l
sudo journalctl -u rtmp-push.service -b --no-pager
```

### 2. 找不到 Python

把 service 里的:

```ini
Environment=PYTHON_BIN=python3
```

改成真实 Python 路径，例如:

```ini
Environment=PYTHON_BIN=/usr/bin/python3
```

或者虚拟环境路径。

### 3. 能启动但没有画面

优先检查:

- `push.py` 里的 `RTMP_URL` 是否正确
- 摄像头索引 `CAMERA_INDEX` 是否正确
- 设备是否能被 OpenCV 打开
- RTMP 服务端 `1935` 端口是否已经启动

## 8. 停止和取消自启

```bash
sudo systemctl stop rtmp-push.service
sudo systemctl disable rtmp-push.service
```
