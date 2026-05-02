基于 **YOLOv8-Pose 姿态估计** + **Mamba-YOLO-World 开放词汇检测** 的实时视频分析系统。

## 目录结构

```
algorithm/
├── manage.py                 # Flask 入口 (端口 6006)
├── config.py                 # 配置文件 (后端URL、流地址)
├── requirements.txt          # Python 依赖
│
├── algo/                     # 核心流程
│   ├── videoProcess.py       # 视频处理主循环 (拉流→推理→报警→推流)
│   ├── yolov8n-pose.engine   # ⚠️ 需生成: YOLOv8 姿态估计模型 (TensorRT) 依赖显卡型号
│   └── mamba2_yolo_world_s.pth  # ⚠️ 需下载: Mamba-YOLO-World 权重
│
├── Yolov8/                   # AI 模型封装
│   ├── Yolov8_Pose.py        # 姿态估计 + 行为识别 (跌倒/打架/挥手/禁区)
│   ├── mamba_yolo.py         # Mamba-YOLO-World 开放词汇检测器封装
│   ├── utils.py              # 图像预处理工具
│   └── utils1.py             # 画框与标注工具
│
├── Mamba-YOLO-World/         # Mamba-YOLO-World 源码 (ICASSP 2025 Oral)
│   ├── configs/              # 模型配置文件
│   ├── yolo_world/           # 模型核心代码
│   └── third_party/mmyolo/   # mmyolo 依赖
│
├── controller/               # Flask API 接口
│   └── monitorController.py  # 检测类型切换、禁区设置、获取帧
│
├── service/                  # 业务逻辑
│   └── AlarmService.py       # 报警推送 (POST → Java 后端)
│
├── common/                   # 共享状态
│   └── monitor.py            # TYPE_LIST (12项检测开关)、帧缓存队列
│
└── util/                     # 工具类
    ├── Logger.py             # 日志
    └── UploadCos.py          # 视频片段上传 (腾讯云COS)
```

## 🔧 环境要求

- **操作系统**: Linux (mamba-ssm 不支持 macOS/Windows)
- **GPU**: NVIDIA GPU + CUDA (推理必须)
- **Python**: 3.8+
- **TensorRT**: 用于 YOLOv8-Pose 加速推理

## 🚀 部署步骤

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

核心依赖版本(不能改):
| 包 | 版本 |
|:---|:---|
| torch | 2.0.0 |
| mmcv | 2.0.1 |
| mmdet | 3.3.0 |
| mmyolo | 0.6.0 |
| mamba-ssm | 2.1.0 |

### 2. 下载 Mamba-YOLO-World 权重

从以下地址下载 **pretrain** 版本 (保留开放词汇能力):

- HuggingFace: https://huggingface.co/Xuan-World/Mamba-YOLO-World
- 夸克网盘: https://pan.quark.cn/s/dce0710ffcec

下载 `MambaYOLOWorld_s_pretrain_O365&GoldG.pth`，放到:
```
algo/mamba2_yolo_world_s.pth
```

### 3. 生成 YOLOv8-Pose TensorRT 引擎

> ⚠️ `.engine` 文件与 GPU 型号绑定，必须在部署机器上生成

```bash
pip install ultralytics
yolo export model=yolov8n-pose.pt format=engine device=0
mv yolov8n-pose.engine algo/
```
可以试试上面的做法，linux下高版本TensorRT且安装ultralytics应该会报一堆各种不兼容
若失败，尝试使用下载官方onnx文件之后通过convert.py脚本生成engine文件，且指定使用TensorRT 10.x版本，代码用ai做了兼容，不知道低版本能不能用

### 4. 克隆 mmyolo (如未完成)

```bash
cd Mamba-YOLO-World/third_party
git clone https://github.com/open-mmlab/mmyolo.git
```

### 5. 配置后端地址

编辑 `config.py`，修改为实际部署地址:
```python
class DevConfig(Config):
    BACKEND_URL = "http://你的Java后端IP:10115"
    STREAM_URL = "rtsp://你的流媒体服务器IP:1935"
```

### 6. 启动

```bash
python manage.py
```

服务将在 `0.0.0.0:6006` 启动。

## 检测能力 (12 类)

TYPE_LIST 与数据库 `case_type_info` 表严格对齐:

| 索引 | caseType | 检测内容 | 检测方式 | 状态 |
|:---:|:---:|:---|:---|:---:|
| 0 | 1 | 进入危险区域 | 姿态估计 | ✅ |
| 1 | 2 | 烟雾 | Mamba-YOLO | ✅ |
| 2 | 3 | 区域停留 | — | ⏳ |
| 3 | 4 | 摔倒 | 姿态估计 | ✅ |
| 4 | 5 | 明火 | Mamba-YOLO | ✅ |
| 5 | 6 | 吸烟 | — | ⏳ |
| 6 | 7 | 打架 | 姿态估计 | ✅ |
| 7 | 8 | 垃圾乱放 | Mamba-YOLO (扩展) | ⏳ |
| 8 | 9 | 冰面 | Mamba-YOLO (扩展) | ⏳ |
| 9 | 10 | 电动车进楼 | Mamba-YOLO (扩展) | ⏳ |
| 10 | 11 | 载具占用车道 | Mamba-YOLO (扩展) | ⏳ |
| 11 | 12 | 挥手呼救 | 姿态估计 | ✅ |

## 数据流

```
摄像头 RTSP 流
    │
    ▼
videoProcess.py (拉流)
    │
    ├── YOLOv8-Pose ──→ 跌倒 / 打架 / 挥手 / 禁区检测
    │
    ├── Mamba-YOLO-World ──→ 明火 / 烟雾 / 自定义目标检测
    │
    ├── 画框标注 ──→ FFmpeg 推流 ──→ 前端播放
    │
    └── 触发报警 ──→ AlarmService.postAlarm()
                         │
                         ▼
                    POST /api/v1/alarm/receive
                    (cameraId, caseType, clipId)
                         │
                         ▼
                    Java 后端存库 + WebSocket 推送
```

## API 接口

Flask 服务暴露以下 API (前缀 `/api/v1/monitor-device`):

| 方法 | 路径 | 功能 |
|:---|:---|:---|
| POST | `/type` | 更新检测类型开关 (12个布尔值) |
| POST | `/area` | 设置危险区域坐标 |
| GET | `/image` | 获取最新处理帧 (Base64) |

## 注意事项

1. **TensorRT 引擎不可跨 GPU**: 3090 生成的 `.engine` 不能在 4090 上用，反之亦然
2. **Mamba-YOLO 权重选 pretrain 版**: `finetune_COCO` 版锁死 80 类，失去开放词汇能力
3. **扩展新检测类别**: 在 `videoProcess.py` 的 `CUSTOM_DETECTION_PROMPTS` 列表中添加英文 prompt 即可


## Docker网络配置说明

为了让Docker容器内的进程访问宿主机上的服务（端口映射到1935），在Docker容器内使用 `host.docker.internal` 作为主机名。

### 启动Docker容器时：

```bash
# 如果使用Docker Desktop（Windows/Mac），默认支持host.docker.internal
docker run -it your-image-name

# 在Linux上，需要额外配置
docker run -it --add-host=host.docker.internal:host-gateway your-image-name
```

### 配置说明：

- 配置文件中已设置 `STREAM_URL = "rtmp://host.docker.internal:1935"`
- 容器内的videoProcess.py将使用这个地址连接到宿主机上的RTMP服务器
- test.py在宿主机上推送流到localhost:1935，通过端口映射到达RTMP服务器
- videoProcess.py在容器内通过host.docker.internal:1935访问宿主机上的RTMP服务器

### Linux特殊说明：

在Linux上，Docker默认不支持`host.docker.internal`，需要在启动容器时添加：

```bash
--add-host=host.docker.internal:host-gateway
```

### 验证连接：

在容器内执行：
```bash
telnet host.docker.internal 1935
```

如果连接成功，则videoProcess.py应该能够访问到RTMP流。
