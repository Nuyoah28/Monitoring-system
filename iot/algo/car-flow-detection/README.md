# 车流量检测方案说明

## 1. 目标

本文档说明如何在本项目中实现一套可落地的车流量检测方案：

`改进版 YOLOv13-lite + ByteTrack + 虚拟线/多边形区域计数`

当前目录已经补充了一套可直接继续开发的实现骨架：

- `main.py`
  车流量检测主入口，负责加载配置、打开视频源、执行检测跟踪、输出计数结果
- `config/camera.example.json`
  示例配置，包含视频源、模型路径、ByteTrack 配置路径、线和区域规则
- `src/detector.py`
  封装本地改进版 `yolov13-lite` 和 `ByteTrack`
- `src/counter.py`
  实现虚拟线过线计数、区域进出计数、区域占有统计
- `src/aggregator.py`
  实现总量和分钟级聚合
- `src/reporter.py`
  支持输出 JSONL 和可选 HTTP 上报
- `src/visualizer.py`
  负责叠加框、轨迹、规则线、区域和统计结果

最小运行方式如下：

```bash
cd iot/algo/car-flow-detection
py -3 main.py --config config/camera.example.json --show
```

运行前需要先修改 `config/camera.example.json` 中的两个字段：

- `source`
  填本地视频路径、RTMP 地址，或者摄像头索引字符串如 `0`
- `model_path`
  填你训练好的车辆检测权重 `.pt` 路径

说明：

- 当前仓库里没有现成可直接推理的车辆检测 `.pt` 权重，所以 `model_path` 默认留空
- `tracker_path` 已默认指向仓库内置的 `ByteTrack` 配置
- 如果后续要接后端接口，可以继续填写 `http_report.url`

这套方案的核心目标不是只做“看见车”，而是稳定完成以下业务能力：

- 统计单位时间内的车辆通行数量
- 区分 `IN / OUT` 或不同方向的车流
- 支持按类别统计，例如 `car`、`bus`、`truck`
- 支持单线计数、双向计数、多区域计数
- 尽量适配 IoT 边缘端部署，控制模型大小和推理时延

从当前仓库结构看，这条路线和现有代码最兼容：

- 现有训练入口已经基于本地改进版 `yolov13-lite`
- `ultralytics` 分支里已经集成 `track()` 能力
- 已经内置 `ByteTrack`、`BoT-SORT`
- 已经有 `ObjectCounter`、`RegionCounter`、`SpeedEstimator`
- 现有 `iot` 工程整体明显偏向边缘推理和轻量部署

因此，车流量检测最合理的第一步不是引入全新体系，而是复用现有检测主干，在其上补齐跟踪和计数逻辑。

---

## 2. 为什么选择这条方案

### 2.1 为什么不用“只做检测”

如果只对每一帧做车辆检测，再把框数直接当车流量，会遇到几个明显问题：

- 同一辆车会在连续多帧中重复出现，无法直接统计“通过了多少辆”
- 遮挡和短时漏检会让统计结果抖动
- 无法区分车辆是驶入还是驶出
- 无法做跨线、跨区域等事件判断

所以车流量任务必须从“逐帧检测”升级为“检测 + 跟踪 + 事件判定”。

### 2.2 为什么用 ByteTrack

ByteTrack 的优势在于：

- 它是成熟的多目标跟踪方案，工程落地非常广泛
- 它保留低分检测框参与第二轮关联，对短时遮挡和低置信度目标更稳
- 算法复杂度和工程成本都相对可控
- 对“车流统计”这种需求非常合适，因为重点是稳定保持 ID

换句话说，YOLO 负责回答“这一帧哪里有车”，ByteTrack 负责回答“这辆车是不是上一帧那辆车”。

### 2.3 为什么用虚拟线/多边形区域计数

车流量统计本质上是事件统计，最常见的触发方式有两类：

1. 车辆轨迹穿过一条虚拟线
2. 车辆中心点进入一个多边形区域

这两类方式各有适用场景：

- 虚拟线：适合出入口、闸机口、单车道、双向车道
- 多边形区域：适合路口、等待区、停车区、缓冲区、多 lane 统计

因此项目里最好同时支持这两种计数模式。

---

## 3. 与当前仓库的对应关系

本方案可以直接复用以下现有代码和目录。

### 3.1 训练入口

文件：

- `iot/algo/parking_space_occupancy_detection/train_yolov13_lite_eucb.py`

作用：

- 用本地修改后的 `yolov13-lite` 训练检测模型
- 支持自定义数据集 yaml
- 适合作为车流量检测中的“车辆检测器训练入口”

### 3.2 改进版 YOLOv13-lite 结构

文件：

- `iot/algo/parking_space_occupancy_detection/yolov13-lite/ultralytics/cfg/models/v13/yolov13.yaml`

当前分支相对常规 YOLO 的特点：

- 使用 `DSConv`、`DSC3k2` 做轻量化
- 使用 `HyperACE` 做多尺度高阶特征增强
- 使用 `FullPAD_Tunnel` 做特征分发
- 用 `EUCB` 替换上采样路径中的普通 `nn.Upsample`

这意味着它本身就是偏轻量、偏边缘端、兼顾精度的一套检测主干，适合作为车流量场景的车辆检测 backbone。

### 3.3 跟踪入口

文件：

- `iot/algo/parking_space_occupancy_detection/yolov13-lite/ultralytics/engine/model.py`
- `iot/algo/parking_space_occupancy_detection/yolov13-lite/ultralytics/trackers/byte_tracker.py`
- `iot/algo/parking_space_occupancy_detection/yolov13/ultralytics/cfg/trackers/bytetrack.yaml`

作用：

- `model.track()` 提供目标跟踪能力
- `ByteTrack` 负责检测框关联、ID 分配、轨迹维护
- `bytetrack.yaml` 负责跟踪阈值配置

### 3.4 现成计数能力

文件：

- `iot/algo/parking_space_occupancy_detection/yolov13-lite/ultralytics/solutions/object_counter.py`
- `iot/algo/parking_space_occupancy_detection/yolov13-lite/ultralytics/solutions/region_counter.py`
- `iot/algo/parking_space_occupancy_detection/yolov13-lite/ultralytics/solutions/solutions.py`

作用：

- `BaseSolution.extract_tracks()` 会调用 `self.model.track(...)`
- `ObjectCounter` 已实现虚拟线/多边形区域上的 `IN / OUT` 计数思路
- `RegionCounter` 已实现多区域中心点落区统计思路

它们已经足够作为车流量模块的直接参考，甚至可以在此基础上裁剪成你们自己的业务版实现。

---

## 4. 总体实现架构

推荐将车流量功能拆为 6 个层次：

1. 视频输入层
2. 检测层
3. 跟踪层
4. 事件判定层
5. 统计聚合层
6. 数据输出层

对应的数据流如下：

```text
摄像头 / 视频流
    ↓
视频解码与抽帧
    ↓
YOLOv13-lite 检测车辆框
    ↓
ByteTrack 关联每一帧目标，生成稳定 track_id
    ↓
根据车辆轨迹判断是否过线 / 进区 / 出区
    ↓
更新实时计数、分钟级流量、分类统计
    ↓
结果叠加到画面 / 写入本地 / 上报后端
```

---

## 5. 模块详细设计

## 5.1 视频输入层

职责：

- 从 RTMP、本地文件、USB 摄像头或 IPC 拉流
- 解码为逐帧图像
- 控制帧率、分辨率、重连策略

建议：

- 对车流统计来说，不一定需要满帧处理
- 一般 `10 FPS` 到 `15 FPS` 已经足够
- 如果边缘设备算力紧张，可以先降到 `640x640` 或按宽边缩放

输入层需要输出：

- 当前帧图像 `frame`
- 时间戳 `timestamp`
- 视频源 ID `camera_id`

---

## 5.2 检测层

职责：

- 识别画面中的车辆目标
- 给出 `bbox + cls + conf`

推荐检测类别：

- `car`
- `bus`
- `truck`
- `motorcycle`

是否保留 `person`、`bicycle` 等类别，取决于业务是否需要混行分析。

### 5.2.1 检测模型选择

优先建议：

- 继续使用当前改进版 `YOLOv13-lite`

原因：

- 与现有训练脚本一致
- 轻量化结构更适合 IoT 边缘端
- 后续导出 ONNX / MNN 路径更自然

### 5.2.2 数据集准备

车流量统计虽然最终做的是计数，但最底层仍然需要检测模型训练，因此要准备车辆检测数据。

标注建议：

- 只标车身目标，不标车影
- 遮挡车辆尽量分别标注
- 保持同一类别标注标准一致
- 尽量覆盖白天、夜晚、逆光、雨天、拥堵、空旷、近景、远景

如果后续要区分车型，训练阶段就要确保类别定义足够清晰。

---

## 5.3 跟踪层

职责：

- 在连续帧之间关联同一辆车
- 给每辆车分配稳定的 `track_id`
- 在短时漏检后尽量保持轨迹连续

### 5.3.1 ByteTrack 的输入输出

输入：

- 当前帧检测结果 `bbox, score, cls`

输出：

- 带有 `track_id` 的目标框

示意：

```text
第 1 帧：car bbox A -> track_id = 7
第 2 帧：car bbox A' -> track_id = 7
第 3 帧：car bbox A'' -> track_id = 7
```

这样后面的计数层才能知道“这是同一辆车在移动”，而不是 3 辆新车。

### 5.3.2 跟踪配置建议

你们当前本地 `bytetrack.yaml` 已提供以下关键参数：

- `track_high_thresh`
- `track_low_thresh`
- `new_track_thresh`
- `track_buffer`
- `match_thresh`

实践建议：

- 检测置信度较稳时，可适度提高 `track_high_thresh`
- 遮挡较多时，可适度增大 `track_buffer`
- 车辆密集、误匹配多时，可微调 `match_thresh`

一个常见调参原则是：

- 先保证“不要频繁换 ID”
- 再处理“不要漏掉过线事件”

因为对车流统计来说，偶尔框抖动影响不大，但 ID 抖动会直接导致重复计数或漏计。

---

## 5.4 轨迹缓存层

职责：

- 为每个 `track_id` 保存历史中心点
- 给过线判断和方向判断提供轨迹依据

每条轨迹至少需要保存：

- `track_id`
- `cls`
- `last_bbox`
- `history_points`
- `last_timestamp`
- `counted_flags`

推荐结构示例：

```python
tracks_state = {
    7: {
        "cls": "car",
        "history": [(x1, y1), (x2, y2), (x3, y3)],
        "last_frame_id": 1234,
        "crossed_lines": set(),
        "entered_regions": set(),
    }
}
```

注意点：

- 历史点不用保存太长，通常保留最近 `20` 到 `30` 个点即可
- 如果某个 `track_id` 长时间未出现，应及时清理
- 如果一辆车已经在某条线完成过一次计数，应避免重复计数

---

## 5.5 事件判定层

这一层是车流量模块的核心，它把“目标轨迹”转换成“计数事件”。

主要包括两种实现方式：

- 虚拟线计数
- 多边形区域计数

## 5.5.1 虚拟线计数

### 原理

在画面中定义一条线段，例如入口横线：

```text
(x1, y1) -------- (x2, y2)
```

对每辆车取连续两帧中心点：

- 上一帧中心点 `prev_point`
- 当前帧中心点 `curr_point`

如果线段 `prev_point -> curr_point` 与虚拟线相交，就认为车辆发生了一次“过线事件”。

### 为什么必须结合 track_id

如果没有 `track_id`，你无法确定前后两个点是不是同一辆车。

所以判断逻辑一定是：

1. 先由 ByteTrack 给出稳定 `track_id`
2. 再对该 `track_id` 的连续位置做过线检测

### 如何判断方向

方向通常由过线前后的相对位置决定。

常见做法：

- 对横向线：比较 `y` 的变化
- 对纵向线：比较 `x` 的变化
- 对任意斜线：使用向量叉积或点在线两侧的符号变化

推荐工程上采用更稳的通用方法：

1. 为虚拟线定义法向量
2. 分别计算 `prev_point` 和 `curr_point` 位于线的哪一侧
3. 从一侧跨到另一侧时触发计数
4. 根据跨越方向判定 `IN` 或 `OUT`

### 虚拟线计数伪代码

```python
for each tracked object:
    prev_point = history[-2]
    curr_point = history[-1]

    if has_crossed(prev_point, curr_point, line):
        if track_id not in counted_line_ids[line_id]:
            direction = get_cross_direction(prev_point, curr_point, line)
            if direction == "IN":
                in_count += 1
            else:
                out_count += 1
            counted_line_ids[line_id].add(track_id)
```

### 适用场景

- 停车场入口
- 停车场出口
- 单车道门岗
- 小区闸口
- 园区出入口

---

## 5.5.2 多边形区域计数

### 原理

在画面中定义一个闭合多边形区域，例如等待区或统计区。

然后判断：

- 车辆中心点是否进入区域
- 车辆是否从区域外进入区域内
- 车辆是否从区域内离开

### 两种常用统计口径

#### 口径 A：瞬时占有数

统计“当前这一帧区域内有多少辆车”。

做法：

- 对每个检测框取中心点
- 判断该点是否在区域内
- 在区域内则 `count += 1`

这个口径适合：

- 路口排队长度
- 某区域拥挤程度
- 某段待行车辆数

#### 口径 B：进入次数 / 离开次数

统计“有多少辆车进入过这个区域”。

做法：

- 为每个 `track_id` 记录上一次是否在区域内
- 状态从 `False -> True` 算一次进入
- 状态从 `True -> False` 算一次离开

这个口径适合：

- 车流方向统计
- 路段通行事件统计
- 区域级出入分析

### 多边形计数伪代码

```python
for each tracked object:
    prev_inside = track_state[track_id]["inside_region"][region_id]
    curr_inside = point_in_polygon(curr_point, polygon)

    if not prev_inside and curr_inside:
        region_enter_count += 1
    elif prev_inside and not curr_inside:
        region_exit_count += 1

    track_state[track_id]["inside_region"][region_id] = curr_inside
```

### 适用场景

- 路口渠化区
- 停车场待入场缓冲区
- 出入口前的排队统计区
- 某条车道专属统计区

---

## 5.6 统计聚合层

职责：

- 把单次事件聚合成业务统计结果

常见聚合维度：

- 当前帧区域内车辆数
- 当前分钟车流量
- 当前小时车流量
- 按方向统计 `IN / OUT`
- 按类别统计 `car / bus / truck`
- 按摄像头统计

推荐保存的字段：

- `camera_id`
- `timestamp`
- `line_id` 或 `region_id`
- `direction`
- `vehicle_class`
- `track_id`
- `event_type`

其中：

- `event_type` 可定义为 `cross_line`、`enter_region`、`exit_region`

分钟级聚合示例：

```text
2026-04-30 10:21
camera_01
入口线 line_A
car: IN 23, OUT 5
bus: IN 2, OUT 0
truck: IN 1, OUT 0
```

---

## 5.7 数据输出层

输出方式可以有三类：

1. 画面叠加
2. 本地日志 / 文件
3. 后端接口上报

### 5.7.1 画面叠加

适合调试和演示：

- 检测框
- `track_id`
- 轨迹线
- 虚拟线 / 多边形区域
- 当前计数

### 5.7.2 本地输出

适合离线分析：

- 保存 csv
- 保存 json
- 保存标注后视频

### 5.7.3 后端上报

适合和现有系统联动：

- 定时上报分钟级统计
- 事件触发时上报单次通行记录

如果后端已经有环境、车位相关表结构，车流量也可以单独扩展：

- `traffic_flow_record`
- `traffic_event_record`
- `camera_region_config`

---

## 6. 推荐工程落地方式

建议在 `iot/algo/car-flow-detection` 下按下面方式组织：

```text
car-flow-detection/
├── README.md
├── config/
│   ├── cameras.example.json
│   ├── regions.example.json
│   └── tracker.example.yaml
├── docs/
│   ├── data-format.md
│   └── tuning-guide.md
├── scripts/
│   ├── run_flow_demo.py
│   ├── evaluate_flow.py
│   └── export_model.py
├── src/
│   ├── detector.py
│   ├── tracker.py
│   ├── counter.py
│   ├── region.py
│   ├── aggregator.py
│   └── reporter.py
└── samples/
    ├── demo.mp4
    └── region_draw.json
```

模块职责建议如下。

### `detector.py`

职责：

- 加载 YOLOv13-lite 模型
- 负责推理前处理和推理后处理

### `tracker.py`

职责：

- 封装 `model.track()` 或单独的跟踪接口
- 输出带 `track_id` 的目标对象

### `counter.py`

职责：

- 实现过线计数
- 实现进区出区计数
- 防止同一 `track_id` 重复计数

### `region.py`

职责：

- 解析虚拟线和多边形配置
- 提供几何判断函数

### `aggregator.py`

职责：

- 维护分钟级、小时级统计窗口
- 按相机、方向、类别聚合

### `reporter.py`

职责：

- 本地保存
- HTTP 上报
- MQTT 上报

---

## 7. 推荐实现步骤

为了降低风险，建议分 4 个阶段推进。

## 阶段 1：单视频离线验证

目标：

- 先在本地视频上跑通完整流程

内容：

- 读取本地视频
- 使用改进版 `YOLOv13-lite`
- 启用 `ByteTrack`
- 画一条虚拟线
- 统计 `IN / OUT`
- 导出带标注视频

验收标准：

- 单辆车不会重复计数
- 双向车流能分开统计
- 统计结果肉眼基本一致

## 阶段 2：多边形区域统计

目标：

- 支持等待区、路口区、车道区统计

内容：

- 增加多区域配置
- 支持瞬时区域数量
- 支持区域进入次数和离开次数

验收标准：

- 区域内车辆数稳定
- 车辆进入和离开事件准确

## 阶段 3：实时流接入

目标：

- 接入 RTMP 或 IPC

内容：

- 增加拉流和重连
- 增加实时可视化
- 增加统计周期上报

验收标准：

- 连续运行稳定
- 流断开后可自动恢复

## 阶段 4：边缘端部署优化

目标：

- 提升吞吐并降低资源占用

内容：

- 导出 ONNX 或 MNN
- 降低输入分辨率
- 控制帧率
- 限制类别数

验收标准：

- 在目标硬件上达到可接受帧率
- 统计准确率保持稳定

---

## 8. 关键实现细节

## 8.1 中心点还是底边中点

对于车辆计数，建议优先使用 `bbox` 的底边中点，而不是几何中心点。

原因：

- 车辆在透视场景中，高度变化明显
- 中心点容易受车身高度、遮挡影响
- 底边中点更接近车轮接地点，更符合“是否过线”的视觉逻辑

建议：

```python
anchor_x = (x1 + x2) / 2
anchor_y = y2
```

如果场景是俯视角或高位监控，中心点也可以接受。

## 8.2 防重复计数

必须对每个 `track_id` 做“已计数状态”控制。

例如：

- 同一辆车穿过同一条线后，不应再次触发同方向计数
- 同一辆车在区域边界抖动时，不应连续进入、离开、再进入

解决方法：

- 为每个 `track_id` 记录已触发的 `line_id`
- 为每个 `region_id` 做状态机转换
- 对边界抖动增加最小位移阈值或冷却帧数

## 8.3 遮挡与 ID 切换

这是车流统计最常见的误差来源。

表现：

- 一辆车被跟踪成两个 `track_id`
- 一辆车短暂丢失后重新出现，被当成新车

解决思路：

- 调整 `ByteTrack` 阈值
- 提高检测稳定性，减少漏检
- 对关键计数线位置尽量选择无遮挡区域
- 如果场景非常拥挤，可后续评估 `BoT-SORT`

## 8.4 线的位置不要贴得太近

虚拟线最好不要画在：

- 车辆刚进入画面的边缘
- 遮挡特别严重的位置
- 车辆转向最剧烈的位置

更好的放置原则：

- 车辆轨迹相对稳定
- 目标尺寸适中
- 遮挡相对较少

## 8.5 统计周期不要只看逐帧

业务侧真正关心的通常不是“这一帧多少辆”，而是：

- 每分钟流量
- 近 5 分钟趋势
- 峰值时段

因此输出层应该天然支持时间窗口聚合。

---

## 9. 与现有 `ObjectCounter` / `RegionCounter` 的关系

本项目完全可以参考现有实现思路，但建议不要直接原样照搬到生产版。

原因如下：

### 9.1 现有 `ObjectCounter` 的优点

- 已具备基本的线计数和多边形计数逻辑
- 已经打通 `track -> history -> count` 的链路
- 很适合作为快速原型

### 9.2 现有 `ObjectCounter` 的局限

- 更偏通用 demo 方案
- 方向判断相对简化
- 统计状态结构还不够业务化
- 没有专门为多摄像头、多规则、多周期上报设计

### 9.3 现有 `RegionCounter` 的特点

- 更适合做“某区域当前有多少目标”
- 默认是逐帧区域内数量统计
- 如果要做“进入次数 / 离开次数”，需要补状态管理

因此更推荐的做法是：

- 保留它们的整体思路
- 在 `car-flow-detection` 目录下做一套面向业务的封装

---

## 10. 推荐配置格式

建议把线和区域配置独立出来，避免写死在代码里。

示例：

```json
{
  "camera_id": "gate_01",
  "source": "rtmp://127.0.0.1/live/gate01",
  "classes": ["car", "bus", "truck"],
  "lines": [
    {
      "id": "entry_line",
      "points": [[220, 420], [980, 420]],
      "direction": "down_is_in"
    }
  ],
  "regions": [
    {
      "id": "waiting_area",
      "points": [[180, 350], [1040, 350], [1080, 520], [140, 520]],
      "mode": "occupancy"
    },
    {
      "id": "entry_zone",
      "points": [[260, 300], [960, 300], [1010, 430], [210, 430]],
      "mode": "enter_exit"
    }
  ]
}
```

这样后续前端或运维工具也更容易做区域绘制和配置下发。

---

## 11. 伪代码示例

下面给出一套更接近工程代码的简化流程。

```python
model = load_yolov13_lite_model(weights)
tracker_cfg = load_tracker_cfg("bytetrack.yaml")
counter = FlowCounter(lines=line_configs, regions=region_configs)
aggregator = FlowAggregator()

for frame, ts in video_stream:
    results = model.track(
        source=frame,
        persist=True,
        tracker=tracker_cfg,
        classes=vehicle_class_ids,
        conf=0.25,
        iou=0.5,
    )

    tracked_objects = parse_results(results)

    for obj in tracked_objects:
        track_id = obj.track_id
        cls_name = obj.cls_name
        bbox = obj.bbox
        anchor = bottom_center(bbox)

        counter.update_track(track_id, cls_name, anchor, ts)

        events = counter.check_events(track_id)
        for event in events:
            aggregator.add_event(
                camera_id=camera_id,
                timestamp=ts,
                event_type=event.type,
                direction=event.direction,
                vehicle_class=cls_name,
                rule_id=event.rule_id,
            )

    frame = draw_visuals(frame, tracked_objects, counter.current_stats())
    output_frame(frame)

    if aggregator.should_flush(ts):
        report(aggregator.flush())
```

---

## 12. 部署建议

## 12.1 原型阶段

建议先用 Python 跑通：

- 开发快
- 便于调参与验证
- 能直接复用现有 `ultralytics` 分支

## 12.2 边缘端落地阶段

后续可以分两种方向：

### 方向 A：继续 Python，但导出轻量模型

- 导出 ONNX
- 导出 MNN
- 降低分辨率和 FPS

优点：

- 迁移成本低

### 方向 B：把推理和计数逻辑逐步迁到 C++

- 底层推理走 MNN / ONNXRuntime
- 规则层保留为轻量 C++ 模块

优点：

- 更符合长期 IoT 部署形态
- 更稳定、资源更可控

如果你们后续希望把车流量功能真正并入 `iot/src` 主程序，方向 B 会更契合整体工程风格。

---

## 13. 评估指标建议

做车流量模块时，不要只看检测 `mAP`，还要看计数指标。

建议至少记录：

- 检测精度：`Precision`、`Recall`、`mAP`
- 跟踪指标：`ID Switch`、`MOTA`、`IDF1`
- 计数指标：`绝对误差`、`相对误差`、`漏计数`、`重复计数`

业务上最关键的是：

- 每分钟车流量误差
- 进出方向误差
- 分车型统计误差

因为最终交付的不是检测框，而是统计结果。

---

## 14. 常见问题

### 问题 1：车辆压线但没有计数

可能原因：

- 跟踪点选取不合适
- 线画得太靠前或太靠后
- 某几帧漏检导致轨迹断裂

处理建议：

- 改用底边中点
- 调整线位置
- 优化检测阈值和跟踪阈值

### 问题 2：同一辆车被统计两次

可能原因：

- `track_id` 发生切换
- 没有做已计数去重
- 车辆在边界附近来回抖动

处理建议：

- 增强去重状态
- 增加冷却机制
- 重新调 `ByteTrack`

### 问题 3：拥堵时统计误差明显变大

可能原因：

- 遮挡严重
- 检测漏框
- 轨迹重叠导致 ID 不稳定

处理建议：

- 优化检测模型
- 增强训练数据中的拥堵场景
- 关键位置改成区域计数而不是单线计数

---

## 15. 最终建议

如果当前目标是“尽快做出一个能用的车流量检测模块”，推荐实施顺序如下：

1. 先复用当前改进版 `YOLOv13-lite` 做车辆检测
2. 直接启用 `ByteTrack`
3. 先做一条虚拟线的 `IN / OUT` 统计
4. 验证稳定后再扩展多边形区域统计
5. 最后再接入实时流和后端上报

这样做的优点是：

- 复用现有仓库能力最多
- 新增代码量最可控
- 最快看到车流统计结果
- 后续扩展到测速、排队长度、拥堵分析也顺畅

---

## 16. 后续可扩展方向

在这套方案稳定后，可以继续扩展：

- 车辆测速
- 排队长度估计
- 车道级流量统计
- 异常停车检测
- 拥堵告警
- 逆行检测
- 红绿灯路口分方向统计

这些功能大多仍然建立在同一条基础链路上：

`检测 -> 跟踪 -> 轨迹 -> 规则事件 -> 聚合统计`

因此先把这条主链路做扎实，是最划算的路径。
