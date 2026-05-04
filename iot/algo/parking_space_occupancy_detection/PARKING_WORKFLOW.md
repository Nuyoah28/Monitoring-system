# 车位检测流程说明

当前车位检测采用基于现有数据集的分类方案，不再使用 YOLO 检测车辆框。

## 整体流程

1. 使用 `mask_crop.png` 或 `mask_1920_1080.png` 标出固定摄像头画面中的车位区域。
2. 程序读取 mask，通过连通域自动提取每个车位的矩形框。
3. 对视频每一帧，按车位框裁剪出每个车位小图。
4. 使用 MobileNetV3 分类器判断裁剪图是 `empty` 还是 `not_empty`。
5. 将每个车位输出为 `free` 或 `occupied`。
6. 生成带标注的视频和逐帧 JSONL 统计结果。

## 当前数据集

数据集位置：

```text
iot/algo/img/parking/clf-data/
  empty/
  not_empty/
```

当前数据集是车位裁剪图分类数据集：

```text
empty      空车位裁剪图
not_empty  有车车位裁剪图
```

它不是 YOLO 检测数据集，不需要 `labels/train`、`labels/val` 这种 YOLO 标注。

## 关键文件

```text
iot/algo/img/parking/mask_crop.png
iot/algo/img/parking/mask_1920_1080.png
iot/algo/img/parking/model/mobilenetv3_parking.pt
iot/algo/img/parking/parking_crop.mp4
iot/algo/img/parking/parking_1920_1080.mp4
```

推理脚本：

```text
iot/algo/parking_space_occupancy_detection/infer_parking_video.py
```

训练脚本：

```text
iot/algo/parking_space_occupancy_detection/train_parking_classifier.py
```

## 训练分类器

进入目录：

```powershell
cd D:/桌面/新建文件夹/Monitoring-system/iot/algo/parking_space_occupancy_detection
```

训练命令：

```powershell
python ./train_parking_classifier.py `
  --data ../img/parking/clf-data `
  --output ../img/parking/model/mobilenetv3_parking.pt `
  --epochs 20 `
  --batch 64 `
  --device 0
```

训练完成后会生成：

```text
iot/algo/img/parking/model/mobilenetv3_parking.pt
```

快速小样本测试训练：

```powershell
python ./train_parking_classifier.py `
  --data ../img/parking/clf-data `
  --output ./runs/parking_classifier/mobilenetv3_smoke.pt `
  --epochs 1 `
  --batch 8 `
  --device cpu `
  --max-per-class 20
```

## 推理视频

裁剪视频推理：

```powershell
python ./infer_parking_video.py `
  --source ../img/parking/parking_crop.mp4 `
  --mask ../img/parking/mask_crop.png `
  --model ../img/parking/model/mobilenetv3_parking.pt `
  --device 0 `
  --output-video ../test_video/processed/parking_classifier_processed.mp4 `
  --jsonl ../test_video/processed/parking_classifier_stats.jsonl
```

完整 1920x1080 视频推理：

```powershell
python ./infer_parking_video.py `
  --source ../img/parking/parking_1920_1080.mp4 `
  --mask ../img/parking/mask_1920_1080.png `
  --model ../img/parking/model/mobilenetv3_parking.pt `
  --device 0 `
  --output-video ../test_video/processed/parking_1920_processed.mp4 `
  --jsonl ../test_video/processed/parking_1920_stats.jsonl
```

只测试前 30 帧：

```powershell
python ./infer_parking_video.py `
  --source ../img/parking/parking_crop.mp4 `
  --mask ../img/parking/mask_crop.png `
  --model ../img/parking/model/mobilenetv3_parking.pt `
  --device 0 `
  --output-video ../test_video/processed/parking_classifier_check.mp4 `
  --jsonl ../test_video/processed/parking_classifier_check.jsonl `
  --max-frames 30
```

## 输出结果

视频输出会画出每个车位框：

```text
红色 occupied
绿色 free
```

JSONL 每一行是一帧，例如：

```json
{
  "frame_index": 0,
  "total_spaces": 14,
  "occupied": 13,
  "free": 1,
  "unknown": 0,
  "occupancy_rate": 0.9285714285714286,
  "spaces": [
    {
      "id": "1",
      "status": "occupied",
      "label": 1,
      "bbox": [70, 0, 131, 56]
    }
  ]
}
```

## 更换摄像头时要做什么

如果换摄像头或画面裁剪方式变化，需要重新制作对应的 mask：

```text
mask_crop.png        对应 parking_crop.mp4 这种裁剪画面
mask_1920_1080.png   对应 1920x1080 原始画面
```

mask 中每个白色连通区域代表一个车位。脚本会自动从 mask 中提取车位框。

如果新摄像头画面和现有数据差异较大，需要重新采集该摄像头下的车位裁剪图，放入：

```text
clf-data/empty
clf-data/not_empty
```

然后重新运行训练脚本生成新的 `mobilenetv3_parking.pt`。
