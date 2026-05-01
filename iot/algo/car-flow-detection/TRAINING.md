# 车流量检测训练说明

## 1. 目标

本文档说明如何为 `iot/algo/car-flow-detection` 训练可用的车辆检测模型，并最终产出可供 [main.py](</D:/桌面/新建文件夹/Monitoring-system/iot/algo/car-flow-detection/main.py:38>) 使用的 `.pt` 权重。

当前推荐训练路线是：

`改进版 YOLOv13-lite（EUCB 版本） -> 车辆检测模型 -> ByteTrack 做跟踪 -> 车流量计数`

也就是说：

- 训练阶段只训练“检测模型”
- 跟踪阶段不重新训练 ByteTrack
- 车流量统计依赖检测框质量和跟踪稳定性

你最终要得到的是一个“车辆检测权重”，再把它填到：

- [camera.example.json](</D:/桌面/新建文件夹/Monitoring-system/iot/algo/car-flow-detection/config/camera.example.json:4>) 的 `model_path`

---

## 2. 当前仓库里的训练入口

你们现成的训练脚本是：

- [train_yolov13_lite_eucb.py](</D:/桌面/新建文件夹/Monitoring-system/iot/algo/parking_space_occupancy_detection/train_yolov13_lite_eucb.py:8>)

它的作用是：

- 默认加载本地修改过的 `yolov13-lite`
- 默认模型结构来自 `cfg/models/v13/yolov13.yaml`
- 支持通过 `--data` 指定数据集 yaml
- 支持通过 `--weights` 加载预训练权重
- 支持设置 `epochs`、`imgsz`、`batch`、`device` 等参数

默认模型配置文件是：

- [yolov13.yaml](</D:/桌面/新建文件夹/Monitoring-system/iot/algo/parking_space_occupancy_detection/yolov13-lite/ultralytics/cfg/models/v13/yolov13.yaml:1>)

---

## 3. 训练前需要明确的事

车流量检测虽然最终做的是“计数”，但训练目标仍然是“车辆检测”。

所以你要训练的不是：

- 过线计数模型
- 区域计数模型
- 跟踪模型

而是一个能稳定检测车辆的目标检测模型。

推荐保留的类别如下：

- `car`
- `motorcycle`
- `bus`
- `truck`

这和当前 [camera.example.json](</D:/桌面/新建文件夹/Monitoring-system/iot/algo/car-flow-detection/config/camera.example.json:6>) 里的：

```json
"class_ids": [2, 3, 5, 7]
```

是一致的，对应 COCO 类别索引：

- `2 -> car`
- `3 -> motorcycle`
- `5 -> bus`
- `7 -> truck`

如果你不需要摩托车，可以自己改成只保留：

```json
"class_ids": [2, 5, 7]
```

同时把训练数据里的类别数和 `names` 一起改掉。

---

## 4. 环境准备

## 4.1 Python 版本建议

推荐：

- Python `3.10` 或 `3.11`

原因：

- 你们本地 `yolov13-lite/requirements.txt` 是围绕较新的 PyTorch 和 Ultralytics 依赖写的
- 太老的 Python 版本容易在 `torch`、`onnxruntime`、`flash-attn` 上卡住

## 4.2 建议创建独立虚拟环境

Windows PowerShell 示例：

```powershell
cd D:\桌面\新建文件夹\Monitoring-system\iot\algo\parking_space_occupancy_detection
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

如果你本机没有 `py -3.11`，也可以用已安装的 `python` 解释器。

## 4.3 安装依赖

仓库里给出的依赖文件是：

- [requirements.txt](</D:/桌面/新建文件夹/Monitoring-system/iot/algo/parking_space_occupancy_detection/yolov13-lite/requirements.txt:1>)

建议安装顺序：

```powershell
cd D:\桌面\新建文件夹\Monitoring-system\iot\algo\parking_space_occupancy_detection
.\.venv\Scripts\Activate.ps1
pip install -r .\yolov13-lite\requirements.txt
pip install -e .\yolov13-lite
```

说明：

- `pip install -e .\yolov13-lite` 很重要，这样训练脚本会优先使用你们本地 fork 的 `ultralytics`
- 如果你不打算使用 `flash_attn`，相关 wheel 安装失败时可以先跳过，再按 CPU 或普通 CUDA 模式训练

## 4.4 GPU 建议

推荐优先用 NVIDIA GPU 训练。

较稳的起步配置：

- 显存 `8GB+`
- `imgsz=640`
- `batch=8` 到 `16`

如果显存不足：

- 降低 `batch`
- 保持 `imgsz=640` 不变优先
- 还不够再考虑 `imgsz=512`

---

## 5. 数据集准备

## 5.1 推荐目录结构

推荐在 `car-flow-detection` 下单独放训练数据相关目录：

```text
iot/algo/car-flow-detection/
├── datasets/
│   └── vehicle_flow/
│       ├── images/
│       │   ├── train/
│       │   └── val/
│       ├── labels/
│       │   ├── train/
│       │   └── val/
│       └── vehicle_flow.yaml
```

也可以把数据集放在别的位置，只要 yaml 里路径写对就行。

## 5.2 标注格式

推荐直接用 YOLO 检测标注格式：

每张图片对应一个同名 `.txt` 文件，每一行格式如下：

```text
class_id x_center y_center width height
```

坐标要求：

- 全部归一化到 `0~1`
- 相对于图片宽高

示例：

```text
0 0.512500 0.683333 0.125000 0.216667
2 0.771875 0.601389 0.184375 0.255556
```

## 5.3 推荐类别定义

如果你想保留 4 类车辆，建议定义：

```yaml
names:
  0: car
  1: motorcycle
  2: bus
  3: truck
```

注意：

- 这是你自己的训练类别索引
- 它不必和 COCO 原始索引一致
- 但训练完成后，`camera.example.json` 里的 `class_ids` 就不能继续用 `[2,3,5,7]`

因为那组值是按 COCO 预训练类目写的。

如果你使用自定义 4 类训练，推理配置应该改成：

```json
"class_ids": [0, 1, 2, 3]
```

如果你只训练 3 类：

```yaml
names:
  0: car
  1: bus
  2: truck
```

则推理配置应改成：

```json
"class_ids": [0, 1, 2]
```

这一点非常关键。

## 5.4 数据集划分建议

建议至少：

- `train` 70%
- `val` 20%
- `test` 10% 或者先不单独切，后面补

如果当前数据量不大：

- 也可以先用 `train / val`

## 5.5 采样建议

车流量场景训练集最好覆盖：

- 白天 / 夜晚
- 晴天 / 阴天 / 雨天
- 入口 / 出口 / 主路 / 路口
- 空旷 / 拥堵
- 近距离 / 远距离
- 轻遮挡 / 重遮挡

如果未来要做真实统计，训练集中一定要覆盖：

- 车辆压线场景
- 多车并行
- 车头车尾混合视角
- 大车遮挡小车

---

## 6. 数据集 yaml 怎么写

在推荐目录下，可以新建：

- `iot/algo/car-flow-detection/datasets/vehicle_flow/vehicle_flow.yaml`

示例内容如下：

```yaml
path: D:/桌面/新建文件夹/Monitoring-system/iot/algo/car-flow-detection/datasets/vehicle_flow
train: images/train
val: images/val

names:
  0: car
  1: motorcycle
  2: bus
  3: truck
```

如果你只训练 3 类：

```yaml
path: D:/datasets/vehicle_flow
train: images/train
val: images/val

names:
  0: car
  1: bus
  2: truck
```

说明：

- `path` 可以写绝对路径，也可以写相对路径
- `train` / `val` 是相对于 `path` 的子目录

---

## 7. 是否要用预训练权重

建议要用。

推荐优先级：

1. 使用你们训练好的历史车辆检测权重
2. 使用公开的 YOLO 系列车辆相关权重
3. 最差也尽量用通用预训练权重再微调

原因：

- 车流量项目的重点是快速得到稳定检测器
- 从头训练通常更慢，而且对数据量要求更高

训练脚本支持：

- `--model`
  指定模型结构 yaml 或 `.pt`
- `--weights`
  额外加载预训练权重

最常见的两种方式如下。

### 方式 A：直接从结构 yaml 开始，再加载权重

```powershell
python .\train_yolov13_lite_eucb.py `
  --data ..\car-flow-detection\datasets\vehicle_flow\vehicle_flow.yaml `
  --model .\yolov13-lite\ultralytics\cfg\models\v13\yolov13.yaml `
  --weights D:\weights\vehicle_pretrain.pt `
  --epochs 100 `
  --imgsz 640 `
  --batch 16 `
  --device 0 `
  --workers 8 `
  --project ..\car-flow-detection\runs\train `
  --name vehicle_flow_v1
```

### 方式 B：直接把 `.pt` 当模型入口继续微调

```powershell
python .\train_yolov13_lite_eucb.py `
  --data ..\car-flow-detection\datasets\vehicle_flow\vehicle_flow.yaml `
  --model D:\weights\vehicle_pretrain.pt `
  --epochs 100 `
  --imgsz 640 `
  --batch 16 `
  --device 0 `
  --workers 8 `
  --project ..\car-flow-detection\runs\train `
  --name vehicle_flow_v1
```

---

## 8. 推荐训练命令

在当前仓库下，推荐从这里启动：

```powershell
cd D:\桌面\新建文件夹\Monitoring-system\iot\algo\parking_space_occupancy_detection
.\.venv\Scripts\Activate.ps1
```

### 8.1 标准训练命令

```powershell
python .\train_yolov13_lite_eucb.py `
  --data ..\car-flow-detection\datasets\vehicle_flow\vehicle_flow.yaml `
  --model .\yolov13-lite\ultralytics\cfg\models\v13\yolov13.yaml `
  --epochs 120 `
  --imgsz 640 `
  --batch 16 `
  --device 0 `
  --workers 8 `
  --project ..\car-flow-detection\runs\train `
  --name vehicle_flow_yolov13_lite
```

### 8.2 小显存机器推荐命令

```powershell
python .\train_yolov13_lite_eucb.py `
  --data ..\car-flow-detection\datasets\vehicle_flow\vehicle_flow.yaml `
  --model .\yolov13-lite\ultralytics\cfg\models\v13\yolov13.yaml `
  --epochs 120 `
  --imgsz 640 `
  --batch 8 `
  --device 0 `
  --workers 4 `
  --project ..\car-flow-detection\runs\train `
  --name vehicle_flow_small_gpu
```

### 8.3 CPU 训练命令

不推荐长期使用，只适合检查流程能不能跑通：

```powershell
python .\train_yolov13_lite_eucb.py `
  --data ..\car-flow-detection\datasets\vehicle_flow\vehicle_flow.yaml `
  --model .\yolov13-lite\ultralytics\cfg\models\v13\yolov13.yaml `
  --epochs 20 `
  --imgsz 512 `
  --batch 4 `
  --device cpu `
  --workers 2 `
  --project ..\car-flow-detection\runs\train `
  --name vehicle_flow_cpu_smoke
```

### 8.4 中断后继续训练

```powershell
python .\train_yolov13_lite_eucb.py `
  --data ..\car-flow-detection\datasets\vehicle_flow\vehicle_flow.yaml `
  --project ..\car-flow-detection\runs\train `
  --name vehicle_flow_yolov13_lite `
  --resume
```

---

## 9. 训练参数怎么选

## 9.1 `epochs`

建议起步：

- `80` 到 `150`

经验上：

- 数据量小：`80~100`
- 数据量中等：`100~150`
- 数据量大：可以更高，但先看收敛趋势

## 9.2 `imgsz`

建议优先：

- `640`

如果场景里远处小车很多，也可以尝试：

- `960`

但代价是：

- 显存更高
- 训练更慢
- 推理更慢

所以第一版通常还是建议 `640`。

## 9.3 `batch`

按显存动态调整：

- 8GB 显存：先试 `8`
- 12GB 显存：先试 `16`
- 24GB 显存：可尝试 `16` 或更高

## 9.4 `device`

示例：

- `0`
- `0,1`
- `cpu`

## 9.5 `workers`

Windows 下如果你碰到 dataloader 问题，可以先降到：

- `workers=0`
- `workers=2`

---

## 10. 训练输出在哪里

如果你按上面的命令启动，训练结果通常会落在：

```text
iot/algo/car-flow-detection/runs/train/vehicle_flow_yolov13_lite/
```

关键文件包括：

- `weights/best.pt`
  验证集指标最优的权重，推荐推理使用
- `weights/last.pt`
  最后一个 epoch 的权重
- `results.png`
  损失和指标曲线图
- `args.yaml`
  本次训练参数记录

你后续通常用：

- `best.pt`

---

## 11. 训练完成后怎么接到车流量模块

假设你的最佳权重是：

```text
D:\桌面\新建文件夹\Monitoring-system\iot\algo\car-flow-detection\runs\train\vehicle_flow_yolov13_lite\weights\best.pt
```

那么把 [camera.example.json](</D:/桌面/新建文件夹/Monitoring-system/iot/algo/car-flow-detection/config/camera.example.json:4>) 改成：

```json
"model_path": "../runs/train/vehicle_flow_yolov13_lite/weights/best.pt"
```

然后根据你的训练类别同步修改：

```json
"class_ids": [0, 1, 2, 3]
```

或者如果你只训练三类：

```json
"class_ids": [0, 1, 2]
```

不要继续保留默认的：

```json
"class_ids": [2, 3, 5, 7]
```

因为那是按 COCO 原始类别编号写的。

---

## 12. 如何验证训练结果

最直接的办法不是先看论文指标，而是先跑你们自己的车流视频。

### 12.1 用车流量主程序验证

```powershell
cd D:\桌面\新建文件夹\Monitoring-system\iot\algo\car-flow-detection
py -3 main.py --config .\config\camera.example.json --show
```

观察重点：

- 小车、公交、卡车是否都能稳定框出
- 遮挡后是否还能恢复
- 压线前后的框是否稳定
- 漏检是否明显影响后续 ByteTrack

### 12.2 业务上重点看什么

对车流项目来说，不只看检测精度，还要看：

- 漏检率
- 重复检出率
- 遮挡时稳定性
- 小目标车辆表现
- 逆光和夜间表现

因为这些会直接影响：

- 跟踪稳定性
- 过线计数准确率
- 区域占有统计

---

## 13. 推荐训练策略

## 13.1 第一阶段：先训练一个能用的车辆检测器

建议：

- 类别数先少一点
- 不要一开始就细分太多车型

例如先做：

- `car`
- `bus`
- `truck`

等主链路稳定后，再考虑：

- `motorcycle`
- `van`
- `pickup`
- `special_vehicle`

## 13.2 第二阶段：用真实车流视频做困难样本补充

第一次训练后，拿你们自己的真实视频跑：

- 看哪里漏检最严重
- 看哪里误检最多
- 补采这些场景
- 继续微调

最有效的提升方法通常不是调一堆超参，而是补困难数据。

## 13.3 第三阶段：围绕计数位置做针对性强化

对于车流统计，最重要的是：

- 虚拟线附近的检测稳定性
- 区域边界附近的检测稳定性

所以标数据时尤其要多保留：

- 压线车辆
- 贴边车辆
- 进出区域瞬间车辆

---

## 14. 常见问题

### 14.1 `model_path` 和 `class_ids` 对不上

表现：

- 明明训练了自己的 3 类或 4 类模型
- 结果主程序里还用默认 `[2,3,5,7]`
- 推理过滤就会错

解决：

- 训练了几类，就按你自己的类别索引改 `class_ids`

### 14.2 训练能跑，但检测远处小车很差

解决思路：

- 补远距离样本
- 适当增加 `imgsz`
- 减少过强的数据增强扰动

### 14.3 拥堵场景计数误差大

这往往不是单纯 ByteTrack 的问题，而是检测器本身对遮挡不够稳。

解决思路：

- 增加拥堵遮挡样本
- 保证被遮挡车辆也被正确标注
- 优先提升检测稳定性，再谈跟踪调参

### 14.4 夜间效果差

解决思路：

- 单独采夜间数据
- 提高夜间样本占比
- 必要时分白天/夜间两套权重

---

## 15. 推荐最小闭环

如果你现在想最快把这件事做成，建议按这个顺序：

1. 准备一个 3 类或 4 类车辆检测数据集
2. 写好 `vehicle_flow.yaml`
3. 用 `train_yolov13_lite_eucb.py` 开始训练
4. 拿 `best.pt` 填回 `camera.example.json`
5. 用 `car-flow-detection/main.py` 跑真实视频
6. 回收误检和漏检样本，继续微调

这样是最稳的。

---

## 16. 一组可直接参考的命令

### 环境初始化

```powershell
cd D:\桌面\新建文件夹\Monitoring-system\iot\algo\parking_space_occupancy_detection
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r .\yolov13-lite\requirements.txt
pip install -e .\yolov13-lite
```

### 开始训练

```powershell
python .\train_yolov13_lite_eucb.py `
  --data ..\car-flow-detection\datasets\vehicle_flow\vehicle_flow.yaml `
  --model .\yolov13-lite\ultralytics\cfg\models\v13\yolov13.yaml `
  --epochs 120 `
  --imgsz 640 `
  --batch 16 `
  --device 0 `
  --workers 8 `
  --project ..\car-flow-detection\runs\train `
  --name vehicle_flow_yolov13_lite
```

### 训练完成后接回主程序

修改：

- [camera.example.json](</D:/桌面/新建文件夹/Monitoring-system/iot/algo/car-flow-detection/config/camera.example.json:1>)

把：

```json
"model_path": ""
```

改成：

```json
"model_path": "../runs/train/vehicle_flow_yolov13_lite/weights/best.pt"
```

然后确认：

```json
"class_ids": [0, 1, 2, 3]
```

### 运行车流量检测

```powershell
cd D:\桌面\新建文件夹\Monitoring-system\iot\algo\car-flow-detection
py -3 main.py --config .\config\camera.example.json --show
```

---

## 17. 最后建议

对这个项目来说，训练阶段最重要的不是把检测指标卷到极致，而是让模型在“计数关键位置”足够稳。

因此优先级应该是：

1. 检测稳定
2. 遮挡恢复好
3. 压线和进出区域瞬间不漏
4. 再去追求更细的车型区分

如果你愿意，我下一步可以继续帮你把：

- `vehicle_flow.yaml` 模板文件
- 数据集目录模板
- 一个一键训练脚本

也一起补到 `car-flow-detection` 目录里。  
