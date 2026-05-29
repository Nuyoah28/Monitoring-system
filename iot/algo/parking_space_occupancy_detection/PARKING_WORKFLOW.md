# 车位占用分类工作流

当前目录已经从单一的 MobileNetV3 流程整理为统一的车位分类框架，支持以下骨干网络做对比实验：

- `mobilenet_v4_small_custom`
- `mobilenet_v3_small`
- `resnet34`
- `edgenext_x_small`

其中 `mobilenet_v4_small_custom` 是当前仓库内置的 MobileNetV4 风格轻量实现，用于在本地环境里补齐 MobileNetV4 对比项。当前 `yolo13` 环境中的 `timm==0.6.12` 不提供官方 MobileNetV4 预训练模型，所以这里不是官方权重版 MobileNetV4。

## 目录说明

核心脚本：

```text
iot/algo/parking_space_occupancy_detection/
  parking_classifier_lib.py
  train_parking_classifier.py
  compare_parking_classifiers.py
  annotate_parking_images.py
  infer_parking_video.py
```

默认模型输出：

```text
iot/algo/img/parking/model/mobilenetv4_parking.pt
iot/algo/img/parking/model/mobilenetv3_parking.pt
iot/algo/img/parking/model/resnet34_parking.pt
iot/algo/img/parking/model/edgenext_x_small_parking.pt
```

## 数据集

当前推荐数据集根目录：

```text
iot/algo/img/parking/archive (1)
```

支持三类数据组织方式：

1. `flat`
   目录结构为 `empty/` 和 `not_empty/`
2. `cnr_ext`
   使用 `CNR-EXT-Patches-150x150/LABELS/train.txt`、`val.txt`、`test.txt`
3. `cnrpark`
   使用 `CNRPark-Patches-150x150` 中的 `busy/free`

脚本默认会自动识别数据集类型；对 `archive (1)` 会自动识别为 `cnr_ext`。

## 训练单个模型

进入目录：

```powershell
cd D:/桌面/新建文件夹/Monitoring-system/iot/algo/parking_space_occupancy_detection
```

训练 MobileNetV4 风格版本：

```powershell
python ./train_parking_classifier.py `
  --data "../img/parking/archive (1)" `
  --dataset-type cnr_ext `
  --model mobilenet_v4_small_custom `
  --epochs 5 `
  --batch 64 `
  --device 0
```

训练 MobileNetV3：

```powershell
python ./train_parking_classifier.py `
  --data "../img/parking/archive (1)" `
  --dataset-type cnr_ext `
  --model mobilenet_v3_small `
  --epochs 5 `
  --batch 64 `
  --device 0
```

训练 ResNet34：

```powershell
python ./train_parking_classifier.py `
  --data "../img/parking/archive (1)" `
  --dataset-type cnr_ext `
  --model resnet34 `
  --epochs 5 `
  --batch 64 `
  --device 0
```

训练 EdgeNeXt：

```powershell
python ./train_parking_classifier.py `
  --data "../img/parking/archive (1)" `
  --dataset-type cnr_ext `
  --model edgenext_x_small `
  --epochs 5 `
  --batch 64 `
  --device 0
```

如果不显式传 `--output`，脚本会按模型名自动保存到 `../img/parking/model/` 下的对应文件。

## 多模型对比实验

运行完整对比：

```powershell
python ./compare_parking_classifiers.py `
  --data "../img/parking/archive (1)" `
  --dataset-type cnr_ext `
  --models mobilenet_v4_small_custom,mobilenet_v3_small,resnet34,edgenext_x_small `
  --epochs 5 `
  --batch 64 `
  --device 0 `
  --output-json ./runs/parking_classifier/compare_results_v2.json `
  --summary-md ./runs/parking_classifier/compare_summary_v2.md `
  --checkpoint-dir ./runs/parking_classifier/models
```

输出内容：

- `compare_results_v2.json`：完整指标、训练历史、推荐模型
- `compare_summary_v2.md`：Markdown 汇总表
- `runs/parking_classifier/models/*.pt`：每个模型的 checkpoint

如果在 Windows 环境里遇到 `PermissionError: [WinError 5]` 且栈里指向 `DataLoader` 多进程队列，可以把 `--workers` 改成 `0`。

快速冒烟测试：

```powershell
python ./compare_parking_classifiers.py `
  --data "../img/parking/archive (1)" `
  --dataset-type cnr_ext `
  --models mobilenet_v4_small_custom,mobilenet_v3_small,resnet34,edgenext_x_small `
  --epochs 1 `
  --batch 4 `
  --device cpu `
  --workers 0 `
  --max-samples-per-split 8 `
  --no-pretrained `
  --output-json ./runs/parking_classifier/compare_results_smoke_v2.json `
  --summary-md ./runs/parking_classifier/compare_summary_smoke_v2.md `
  --checkpoint-dir ./runs/parking_classifier/smoke_models
```

## 图片标注与推理

标注脚本支持在 `iot/algo/test_img` 下对图片画与图像边框平行的矩形框，然后直接用训练好的分类模型推理，并把结果图继续保存回 `test_img`。

示例：

```powershell
python ./annotate_parking_images.py `
  --input-dir ../test_img `
  --model ../img/parking/model/mobilenetv4_parking.pt `
  --device 0
```

如果你希望继续沿用旧模型，也可以把 `--model` 改成：

```text
../img/parking/model/mobilenetv3_parking.pt
../img/parking/model/resnet34_parking.pt
../img/parking/model/edgenext_x_small_parking.pt
```

## 视频推理

视频推理脚本会读取 mask 中每个白色连通区域对应的车位框，裁剪后送入分类模型，再输出带框视频和逐帧统计。

示例：

```powershell
python ./infer_parking_video.py `
  --source ../img/parking/parking_crop.mp4 `
  --mask ../img/parking/mask_crop.png `
  --model ../img/parking/model/mobilenetv4_parking.pt `
  --device 0 `
  --output-video ../test_video/processed/parking_classifier_processed.mp4 `
  --jsonl ../test_video/processed/parking_classifier_stats.jsonl
```

完整分辨率视频示例：

```powershell
python ./infer_parking_video.py `
  --source ../img/parking/parking_1920_1080.mp4 `
  --mask ../img/parking/mask_1920_1080.png `
  --model ../img/parking/model/mobilenetv4_parking.pt `
  --device 0 `
  --output-video ../test_video/processed/parking_1920_processed.mp4 `
  --jsonl ../test_video/processed/parking_1920_stats.jsonl
```

## 旧版 MobileNetV3 文件说明

旧流程并没有删除，`mobilenet_v3_small` 现在作为正式对比基线保留。

- 老的 V3 权重命名：`mobilenetv3_parking.pt`
- 新默认主推模型：`mobilenetv4_parking.pt`
- 推理脚本已支持从 checkpoint 中自动识别模型类型，不再写死只支持 MobileNetV3

这样你可以直接复用旧权重，也可以把 V3、V4、ResNet34、EdgeNeXt 统一放到同一套训练和推理流程里管理。
