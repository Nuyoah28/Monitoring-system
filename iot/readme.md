# 监控系统项目

本项目演示了在嵌入式/IoT 环境下结合 MNN 神经网络推理、天气监测和报警上报的监控系统。

## 开发阶段服务器配置

- 服务器 IP：`192.168.213.197`
- Java 后端服务端口：`10215`（天气数据与报警均发到该端口）
- RTMP 视频流端口：`1935`（原始视频流通过 RTMP 推送到该端口，例如 `rtmp://192.168.213.197:1935/live/raw`）

> 可以通过设置环境变量 `SERVER_IP`、`JAVA_PORT` 或 `RTMP_PORT` 覆盖以上默认值。

How to use:
```bash
$ mkdir build
$ cd build
$ cmake ..
$ make -j
$ main
```

