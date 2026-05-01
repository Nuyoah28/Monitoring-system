# Ubuntu WiFi Auto Connect

这个目录提供一份 Ubuntu 开机自动连 WiFi 的脚本:

- [connect_preferred_wifi.sh](/d:/桌面/新建文件夹/Monitoring-system/iot/wifi/connect_preferred_wifi.sh)

连接优先级如下:

1. WiFi 名称: `iqoo`
   密码: `12345678`
2. 备用 WiFi 名称: `斯是陋室 为吾德馨`
   密码: `fxbfbxjyczbw327`

脚本逻辑:

- 开机后先扫描附近 WiFi
- 优先连接 `iqoo`
- 如果没扫描到 `iqoo`，则连接 `斯是陋室 为吾德馨`
- 同时会把这两个连接配置为自动连接，并设置优先级

## 适用前提

- Ubuntu 使用 `NetworkManager`
- 系统能使用 `nmcli`

先检查:

```bash
nmcli --version
systemctl status NetworkManager
```

如果没有 `NetworkManager`，先安装:

```bash
sudo apt update
sudo apt install network-manager
```

## 1. 给脚本执行权限

```bash
cd /path/to/Monitoring-system
chmod +x iot/wifi/connect_preferred_wifi.sh
```

## 2. 先手动测试一次

```bash
sudo bash iot/wifi/connect_preferred_wifi.sh
```

查看当前连接:

```bash
nmcli device status
nmcli connection show --active
```

## 3. 配置开机自动执行

在 Ubuntu 上推荐用 `systemd`。

创建服务文件:

```bash
sudo nano /etc/systemd/system/preferred-wifi.service
```

写入下面内容:

```ini
[Unit]
Description=Connect preferred WiFi on boot
Wants=NetworkManager.service
Wants=NetworkManager-wait-online.service
After=NetworkManager.service NetworkManager-wait-online.service

[Service]
Type=oneshot
ExecStart=/bin/bash /path/to/Monitoring-system/iot/wifi/connect_preferred_wifi.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

注意把 `/path/to/Monitoring-system` 替换成你项目的实际绝对路径。

例如如果项目在 `/home/ubuntu/Monitoring-system`，则应写成:

```ini
ExecStart=/bin/bash /home/ubuntu/Monitoring-system/iot/wifi/connect_preferred_wifi.sh
```

## 4. 启用开机自启

```bash
sudo systemctl daemon-reload
sudo systemctl enable preferred-wifi.service
sudo systemctl start preferred-wifi.service
```

## 5. 查看运行状态

```bash
systemctl status preferred-wifi.service
journalctl -u preferred-wifi.service -b
```

## 6. 如果需要取消

```bash
sudo systemctl disable preferred-wifi.service
sudo rm /etc/systemd/system/preferred-wifi.service
sudo systemctl daemon-reload
```

## 补充说明

- 这个脚本把 WiFi 密码直接写在脚本里，部署方便，但明文存储安全性一般。
- 如果后续你要发到公开仓库，建议把密码改成从环境变量或单独配置文件读取。
- 如果系统本身已经由 `NetworkManager` 管理 WiFi，这个脚本主要作用是强化优先连接顺序，并在开机时主动触发连接。
