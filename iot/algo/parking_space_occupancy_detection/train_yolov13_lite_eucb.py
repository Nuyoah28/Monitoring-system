from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parent
    default_model = root / "yolov13-lite" / "ultralytics" / "cfg" / "models" / "v13" / "yolov13.yaml"

    parser = argparse.ArgumentParser(description="Train YOLOv13-lite (EUCB version)")
    # [数据集修改入口] 运行时改这个参数即可切换数据集配置文件
    parser.add_argument("--data", type=str, required=True, help="Dataset yaml path")
    parser.add_argument("--model", type=str, default=str(default_model), help="Model yaml or .pt path")
    parser.add_argument("--weights", type=str, default="", help="Optional pretrained weights (.pt)")
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--device", type=str, default="0", help="CUDA device, e.g. 0 or 0,1 or cpu")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--project", type=str, default="runs/train")
    parser.add_argument("--name", type=str, default="yolov13_lite_eucb")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parent
    yolo_lite_dir = root / "yolov13-lite"

    if not yolo_lite_dir.exists():
        raise FileNotFoundError(f"Cannot find directory: {yolo_lite_dir}")

    # Ensure importing local modified ultralytics from yolov13-lite
    sys.path.insert(0, str(yolo_lite_dir))
    from ultralytics import YOLO  # pylint: disable=import-error,import-outside-toplevel

    model_path = Path(args.model)
    if not model_path.is_absolute():
        model_path = (root / model_path).resolve()

    data_path = Path(args.data)
    if not data_path.is_absolute():
        data_path = (root / data_path).resolve()

    model = YOLO(str(model_path))
    if args.weights:
        weights_path = Path(args.weights)
        if not weights_path.is_absolute():
            weights_path = (root / weights_path).resolve()
        model = model.load(str(weights_path))

    # [训练参数修改入口] 训练轮数、分辨率、batch、设备等都在这里传给 train()
    model.train(
        data=str(data_path),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        project=args.project,
        name=args.name,
        resume=args.resume,
    )


if __name__ == "__main__":
    main()


'''
python parking_space_occupancy_detection/train_yolov13_lite_eucb.py \
  --data ../img/PKLot/data.yaml \
  --epochs 110 \
  --imgsz 640 \
  --batch 32 \
  --device 0 \
  --project parking_space_occupancy_detection/runs_emcad/train \
  --name vehicle_flow_yolov13_lite
'''