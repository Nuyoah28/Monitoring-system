# Model Convert

这个目录用于把 `pt` 模型转换成 `onnx` 和 `mnn`。

## 目录说明

- `export_pt_to_onnx.py`: `pt -> onnx`
- `convert_onnx_to_mnn.py`: `onnx -> mnn`
- `pt_to_mnn.py`: 一次完成 `pt -> onnx -> mnn`

## 默认约定

- 默认示例模型: `iot/algo/yolov13n.pt`
- 默认本地 `ultralytics` 代码: `iot/algo/parking_space_occupancy_detection/yolov13`
- 默认 `MNNConvert` 路径:
  - `iot/MNN/build/MNNConvert.exe`
  - `iot/MNN/build/MNNConvert`

如果你的 `MNNConvert` 在别的位置，可以手动传 `--mnnconvert`。

## 1. pt 转 onnx

在仓库根目录执行:

```powershell
python iot/algo/model-convert/export_pt_to_onnx.py `
  --weights iot/algo/yolov13n.pt `
  --output iot/algo/models/yolov13n.onnx `
  --imgsz 640 `
  --device cpu
```

## 2. onnx 转 mnn

```powershell
python iot/algo/model-convert/convert_onnx_to_mnn.py `
  --onnx iot/algo/models/yolov13n.onnx `
  --output iot/algo/models/yolov13n.mnn
```

## 3. 一键转换 pt 到 mnn

```powershell
python iot/algo/model-convert/pt_to_mnn.py `
  --weights iot/algo/yolov13n.pt `
  --onnx-output iot/algo/models/yolov13n.onnx `
  --mnn-output iot/algo/models/yolov13n.mnn `
  --imgsz 640 `
  --device cpu
```

## 说明

- `pt -> onnx` 依赖本地可用的 `torch` 和 `ultralytics` 环境。
- `onnx -> mnn` 依赖本地可执行的 `MNNConvert`。
- 如果导出失败，优先检查:
  - 模型权重路径是否正确
  - `ultralytics` 代码目录是否存在
  - `MNNConvert` 是否已经编译完成
