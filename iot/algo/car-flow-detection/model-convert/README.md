# Model Convert

这个目录用于把车流量检测模型从 `.pt` 转成 `.onnx` 和 `.mnn`。

## 目录约定

默认模型目录在项目根目录的 `models/` 下：

```text
models/
  pt/      # 输入 PyTorch 权重
  onnx/    # 输出 ONNX 模型
  mnn/     # 输出 MNN 模型
```

当前默认支持这些权重命名：

```text
models/pt/yolov8.pt
models/pt/yolov12.pt
models/pt/yolov13.pt
models/pt/yolov13-eucb.pt
```

脚本会按模型名自动选择本地 Ultralytics 分支：

```text
yolov8.pt       -> yolov13-lite
yolov12.pt      -> yolov12
yolov13.pt      -> yolov13
yolov13-eucb.pt -> yolov13-lite
```

## 一键批量转换

在服务器 `/opt/car-flow-detection` 下执行：

```bash
python ./model-convert/convert_models.py \
  --models-dir ./models \
  --imgsz 960 \
  --device 0 \
  --opset 12 \
  --batch 1 \
  --simplify \
  --overwrite
```

如果你在 Windows PowerShell 下运行，必须有 Windows 版本的 `MNNConvert.exe`。如果当前 `iot/MNN/build/MNNConvert` 是 Linux 编译产物，Windows 会报：

```text
WinError 193: %1 不是有效的 Win32 应用程序
```

这种情况下可以先只导出 ONNX：

```powershell
python ./model-convert/convert_models.py `
  --models-dir ./models `
  --imgsz 960 `
  --device 0 `
  --opset 12 `
  --batch 1 `
  --simplify `
  --overwrite `
  --skip-mnn
```

等 Windows 版 `MNNConvert.exe` 准备好后再转 MNN：

```powershell
python ./model-convert/convert_models.py `
  --models-dir ./models `
  --skip-onnx `
  --overwrite `
  --mnnconvert D:\path\to\MNNConvert.exe
```

转换完成后会生成：

```text
models/onnx/yolov8.onnx
models/onnx/yolov12.onnx
models/onnx/yolov13.onnx
models/onnx/yolov13-eucb.onnx

models/mnn/yolov8.mnn
models/mnn/yolov12.mnn
models/mnn/yolov13.mnn
models/mnn/yolov13-eucb.mnn
```

如果只想转换部分模型：

```bash
python ./model-convert/convert_models.py \
  --weights yolov13-eucb.pt yolov12.pt \
  --imgsz 960 \
  --device 0 \
  --simplify \
  --overwrite
```

## 单模型转换

`.pt -> .onnx -> .mnn`：

```bash
python ./model-convert/pt_to_mnn.py \
  --weights ./models/pt/yolov13-eucb.pt \
  --imgsz 960 \
  --device 0 \
  --simplify
```

默认输出到：

```text
models/onnx/yolov13-eucb.onnx
models/mnn/yolov13-eucb.mnn
```

## 分步转换

只导出 ONNX：

```bash
python ./model-convert/export_pt_to_onnx.py \
  --weights ./models/pt/yolov13-eucb.pt \
  --output ./models/onnx/yolov13-eucb.onnx \
  --ultralytics-dir ./yolov13-lite \
  --imgsz 960 \
  --device 0 \
  --simplify
```

只转换 MNN：

```bash
python ./model-convert/convert_onnx_to_mnn.py \
  --onnx ./models/onnx/yolov13-eucb.onnx \
  --output ./models/mnn/yolov13-eucb.mnn
```

## 测试 ONNX / MNN

转换后可以用同一张图片测试 ONNX 和 MNN 模型：

```bash
python ./model-convert/test_exported_models.py \
  --models-dir ./models \
  --image ./datasets/vehicle_flow/images/val/MVI_20011/img00001.jpg \
  --imgsz 960 \
  --conf 0.25 \
  --iou 0.45 \
  --runs 20
```

如果不传 `--image`，脚本会从 `--data` 的验证集里自动取第一张图：

```bash
python ./model-convert/test_exported_models.py \
  --models-dir ./models \
  --data ./datasets/vehicle_flow.yaml \
  --imgsz 960 \
  --runs 20
```

只测指定模型：

```bash
python ./model-convert/test_exported_models.py \
  --models-dir ./models \
  --weights yolov12 yolov13-eucb \
  --imgsz 960 \
  --runs 20
```

输出内容包括：

```text
latency ms
FPS
output shape
detections count
```

可视化结果会保存到：

```text
outputs/export_test/
```

依赖：

```bash
pip install onnxruntime-gpu pillow pyyaml
```

如果要测试 MNN，还需要 Python 可以 `import MNN`。

## ARMv8 Linux 无 Python 对比测试

如果目标设备不想安装 Python 相关依赖，可以用命令行工具测试：

- ONNX: `onnxruntime_perf_test`
- MNN: `timeProfile.out`

脚本：

```bash
bash ./model-convert/benchmark_exported_cli.sh \
  --models-dir ./models \
  --ort-bin /path/to/onnxruntime_perf_test \
  --mnn-timeprofile /path/to/MNN/build/timeProfile.out \
  --ort-ep cpu \
  --mnn-forward 0 \
  --runs 50
```

四个模型会自动测试：

```text
yolov8
yolov12
yolov13
yolov13-eucb
```

输出日志保存到：

```text
outputs/export_benchmark_cli/logs/
```

汇总文件：

```text
outputs/export_benchmark_cli/summary.tsv
```

如果只测部分模型：

```bash
bash ./model-convert/benchmark_exported_cli.sh \
  --models-dir ./models \
  --ort-bin /path/to/onnxruntime_perf_test \
  --mnn-timeprofile /path/to/MNN/build/timeProfile.out \
  --models yolov12 yolov13-eucb \
  --runs 100
```

MNN 常见后端：

```text
0 = CPU
3 = OpenCL
7 = Vulkan
```

ONNX Runtime 的 `--ort-ep` 取决于你下载/编译的 ONNX Runtime 支持哪些执行后端，常见是：

```text
cpu
acl
nnapi
```

## MNNConvert

脚本会自动查找：

```text
iot/MNN/build/MNNConvert
iot/MNN/build/MNNConvert.exe
iot/MNN/build/Release/MNNConvert
iot/MNN/build/Release/MNNConvert.exe
```

如果 `MNNConvert` 在其他位置，手动传入：

```bash
python ./model-convert/convert_models.py \
  --mnnconvert /path/to/MNNConvert
```

## 常见说明

- `pt -> onnx` 依赖当前 Python 环境里可用的 `torch` 和本项目本地 Ultralytics 代码。
- `onnx -> mnn` 依赖已经编译好的 `MNNConvert`。
- 如果只是先导出 ONNX，可以加 `--skip-mnn`。
- 如果已经有 ONNX，只想转 MNN，可以加 `--skip-onnx`。

## Docker 常见问题

如果在 Docker 里报：

```text
ImportError: libGL.so.1: cannot open shared object file
```

说明容器缺少 OpenCV 运行库，先安装：

```bash
apt-get update && apt-get install -y libgl1 libglib2.0-0
```

如果报：

```text
ImportError: cannot import name 'FastSAM'
```

说明当前 `yolov13` / `yolov13-lite` 是裁剪版代码，`FastSAM` 文件为空。当前脚本只做检测模型导出，已经在本项目里补了 FastSAM 占位导出，不影响 YOLO 检测模型转换。
