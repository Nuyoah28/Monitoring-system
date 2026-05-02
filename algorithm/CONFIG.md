# 配置说明

本文档对应统一配置入口 [config.py](/d:/桌面/新建文件夹/Monitoring-system/algorithm/config.py:1)。

当前 `algorithm` 服务的业务配置已经集中到这一处维护，运行时由 `RuntimeConfig` 统一对外提供。

## 配置加载规则

配置优先级如下：

1. 环境变量
2. `config.py` 中 `DevConfig` / `ProdConfig` 的默认值
3. `Config` 基类默认值

运行环境通过 `APP_CONFIG` 选择：

```bash
APP_CONFIG=dev
APP_CONFIG=prod
```

未设置时默认使用 `dev`。

## 当前入口

- Flask 启动入口: [manage.py](/d:/桌面/新建文件夹/Monitoring-system/algorithm/manage.py:1)
- 统一配置文件: [config.py](/d:/桌面/新建文件夹/Monitoring-system/algorithm/config.py:1)
- 运行时共享配置: [common/monitor.py](/d:/桌面/新建文件夹/Monitoring-system/algorithm/common/monitor.py:1)

## 主要配置分组

### 1. 服务启动

| 配置项 | 说明 | 默认值 |
| --- | --- | --- |
| `APP_CONFIG` | 运行配置名，`dev` 或 `prod` | `dev` |
| `APP_HOST` | Flask 监听地址 | `0.0.0.0` |
| `APP_PORT` | Flask 监听端口 | `6006` |

### 2. 后端与流地址

| 配置项 | 说明 | `dev` 默认值 |
| --- | --- | --- |
| `BACKEND_URL` | Java 后端地址 | `http://host.docker.internal:10215` |
| `STREAM_URL` | 流媒体服务地址 | `rtmp://host.docker.internal:1935` |
| `STREAM_RAW_URL` | Python 拉取原始流地址 | `rtmp://host.docker.internal:1935/live/raw` |
| `STREAM_PROCESSED_URL` | Python 推送处理后视频流地址 | `rtmp://host.docker.internal:1935/live/ai` |
| `TOKEN` | 后端访问令牌 | 空 |

### 3. 点位与检测区域

| 配置项 | 说明 | 默认值 |
| --- | --- | --- |
| `MONITOR_ID` | 摄像头/点位 ID | `1` |
| `LATITUDE` | 纬度 | `0` |
| `LONGITUDE` | 经度 | `0` |
| `TYPE_LIST` | 12 类检测能力开关 | `[False, False, False, True, False, False, True, False, False, False, False, True]` |
| `AREA_LIST` | 危险区域坐标，格式为左上和右下点 | `[(0, 0), (1280, 720)]` |

`TYPE_LIST` 与数据库 `case_type_info` 表中的 `caseType 1~12` 严格对应。

### 4. 视频处理

| 配置项 | 说明 | 默认值 |
| --- | --- | --- |
| `VIDEO_PROCESSING_ENABLED` | 是否启用视频处理 | `True` |
| `VIDEO_CACHE_SIZE` | 视频缓存大小 | `50` |
| `CAPTURE_WIDTH` | 采集宽度 | `1280` |
| `CAPTURE_HEIGHT` | 采集高度 | `720` |
| `DISPLAY_WIDTH` | 显示宽度 | `1280` |
| `DISPLAY_HEIGHT` | 显示高度 | `720` |
| `FRAMERATE` | 采样帧率 | `60` |
| `FLIP_METHOD` | 图像翻转方式 | `0` |
| `WARNING_STREAK_MIN_HITS` | 连续命中多少帧后才认为告警稳定 | `3` |

### 5. Mamba-YOLO 自定义目标

| 配置项 | 说明 | 默认值 |
| --- | --- | --- |
| `CUSTOM_DETECTION_PROMPTS` | 扩展检测 prompt 列表 | `overflow`, `garbage`, `garbage bin`, `bicycle`, `motorcycle` |
| `ENABLE_PROMPT_SYNONYMS` | 是否启用 prompt 同义词扩展 | `False` |

说明：

- `CUSTOM_DETECTION_PROMPTS` 用于在 `fire`、`smoke` 之外增加业务目标。
- `ENABLE_PROMPT_SYNONYMS=True` 时，会在 [Yolov8/mamba_yolo_prompts.py](/d:/桌面/新建文件夹/Monitoring-system/algorithm/Yolov8/mamba_yolo_prompts.py:1) 中扩展同义词组。

### 6. CTR-GCN 动作识别

#### 基础配置

| 配置项 | 说明 | 默认值 |
| --- | --- | --- |
| `ACTION_MODEL_BACKEND` | 动作识别后端 | `ctrgcn` |
| `ACTION_CTR_GCN_ROOT` | CTR-GCN 代码目录 | `algorithm/CTR-GCN` |
| `ACTION_CTR_GCN_FUSION` | 融合模式 | `joint_bone` |
| `ACTION_CTR_GCN_FUSION_MODE` | 融合输出方式 | `logits` |
| `ACTION_CTR_GCN_JOINT_WEIGHTS` | joint 流权重文件 | `algorithm/algo/ctrgcn_joint_w90_ref_lie_vfF5O15_wCE.pt` |
| `ACTION_CTR_GCN_BONE_WEIGHTS` | bone 流权重文件 | `algorithm/algo/ctrgcn_bone_w90_ref_lie_vfF5O15_wCE.pt` |
| `ACTION_CTR_GCN_WEIGHTS` | 单流兼容权重别名 | 默认跟随 `ACTION_CTR_GCN_JOINT_WEIGHTS` |
| `ACTION_CTR_GCN_JOINT_ALPHA` | joint 流权重系数 | `1.0` |
| `ACTION_CTR_GCN_BONE_ALPHA` | bone 流权重系数 | `1.0` |
| `ACTION_LABEL_ORDER` | 动作标签顺序 | `("normal", "fall", "punch", "wave")` |

#### 时序与跟踪配置

| 配置项 | 说明 | 默认值 |
| --- | --- | --- |
| `ACTION_WINDOW_SIZE` | 时序窗口大小 | `90` |
| `ACTION_MIN_FRAMES` | 最少帧数 | `8` |
| `ACTION_SMOOTH` | 平滑窗口 | `4` |
| `ACTION_MAX_TRACKS` | 最大跟踪人数 | `8` |
| `ACTION_TOP_K_TRACKS` | 单次推理保留人数 | `4` |
| `ACTION_INFER_INTERVAL` | 推理间隔帧数 | `1` |
| `ACTION_MAX_MISSING` | 目标最大丢失帧数 | `10` |

#### 跌倒阈值

| 配置项 | 说明 | 默认值 |
| --- | --- | --- |
| `ACTION_FALL_ON_THR` | 跌倒触发阈值 | `0.35` |
| `ACTION_FALL_OFF_THR` | 跌倒释放阈值 | `0.15` |
| `ACTION_FALL_HOLD_FRAMES` | 跌倒保持帧数 | `75` |
| `ACTION_FALL_RELEASE_FRAMES` | 跌倒释放所需连续低分帧数 | `30` |
| `ACTION_FALL_LATCH` | 是否锁定跌倒状态 | `True` |

#### 挥手阈值

| 配置项 | 说明 | 默认值 |
| --- | --- | --- |
| `ACTION_WAVE_ON_THR` | 挥手触发阈值 | `0.40` |
| `ACTION_WAVE_OFF_THR` | 挥手释放阈值 | `0.20` |
| `ACTION_WAVE_CONFIRM_FRAMES` | 挥手确认帧数 | `3` |
| `ACTION_WAVE_RELEASE_FRAMES` | 挥手释放帧数 | `8` |

#### 打架阈值

| 配置项 | 说明 | 默认值 |
| --- | --- | --- |
| `ACTION_PUNCH_ON_THR` | 出拳触发阈值 | `0.45` |
| `ACTION_PUNCH_OFF_THR` | 出拳释放阈值 | `0.20` |
| `ACTION_PUNCH_CONFIRM_FRAMES` | 出拳确认帧数 | `3` |
| `ACTION_PUNCH_RELEASE_FRAMES` | 出拳释放帧数 | `8` |
| `ACTION_FIGHT_DISTANCE_RATIO` | 判定近距离对抗的距离比例 | `1.40` |
| `ACTION_FIGHT_CONFIRM_FRAMES` | 打架确认帧数 | `4` |
| `ACTION_FIGHT_RELEASE_FRAMES` | 打架释放帧数 | `12` |

### 7. 告警缓存与同步

| 配置项 | 说明 | 默认值 |
| --- | --- | --- |
| `ALARM_CACHE_ENABLED` | 是否启用本地告警缓存 | `True` |
| `ALARM_CACHE_DIR` | 告警缓存根目录 | `runtime/alarm_cache` |
| `ALARM_CACHE_DB` | SQLite 文件名 | `alarm_cache.sqlite3` |
| `ALARM_CACHE_CLIP_DIR` | 告警片段目录 | `clips` |
| `ALARM_SYNC_INTERVAL_SECONDS` | 后台同步间隔秒数 | `10` |
| `ALARM_SYNC_BATCH_SIZE` | 单次同步批量大小 | `20` |
| `ALARM_REQUEST_TIMEOUT_SECONDS` | 告警请求超时秒数 | `5` |

### 8. 腾讯云翻译

| 配置项 | 说明 | 默认值 |
| --- | --- | --- |
| `TENCENT_SECRET_ID` | 腾讯云 SecretId | 代码默认值 |
| `TENCENT_SECRET_KEY` | 腾讯云 SecretKey | 代码默认值 |

建议实际部署时使用环境变量覆盖，不要长期保留代码中的默认密钥。

## 配置修改建议

### 本地开发

通常只需要改 `DevConfig`，或直接设置环境变量覆盖：

```bash
set APP_CONFIG=dev
set BACKEND_URL=http://127.0.0.1:10215
set STREAM_RAW_URL=rtmp://127.0.0.1:1935/live/raw
set STREAM_PROCESSED_URL=rtmp://127.0.0.1:1935/live/ai
```

### Linux / Docker

更推荐通过环境变量注入：

```bash
export APP_CONFIG=prod
export APP_HOST=0.0.0.0
export APP_PORT=6006
export BACKEND_URL=http://your-java-service:10215
export STREAM_RAW_URL=rtmp://your-stream-service:1935/live/raw
export STREAM_PROCESSED_URL=rtmp://your-stream-service:1935/live/ai
export ACTION_CTR_GCN_ROOT=/app/algorithm/CTR-GCN
```

## 代码中的配置使用方式

统一写法：

```python
from config import RuntimeConfig as Config

backend_url = Config.BACKEND_URL
```

如果是共享状态模块，当前项目也允许通过 [common/monitor.py](/d:/桌面/新建文件夹/Monitoring-system/algorithm/common/monitor.py:1) 读取运行时镜像值。

## 后续维护建议

- 新增项目配置时，优先加到 [config.py](/d:/桌面/新建文件夹/Monitoring-system/algorithm/config.py:1)
- 避免在业务代码里继续散写 `os.environ.get(...)`
- 如果某个参数是“共享运行态”，再考虑同步到 [common/monitor.py](/d:/桌面/新建文件夹/Monitoring-system/algorithm/common/monitor.py:1)
- 涉及密钥、地址、权重路径的配置，部署时优先用环境变量覆盖
