from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.single_class_dataset import ensure_single_class_dataset


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parent
    default_model = root / "yolov13-lite" / "ultralytics" / "cfg" / "models" / "v13" / "yolov13.yaml"

    parser = argparse.ArgumentParser(description="Train YOLOv13-lite (EUCB version)")
    # [数据集修改入口] 运行时改这个参数即可切换数据集配置文件
    parser.add_argument("--data", type=str, required=True, help="Dataset yaml path")
    parser.add_argument("--model", type=str, default=str(default_model), help="Model yaml or .pt path")
    parser.add_argument("--weights", type=str, default="", help="Optional pretrained weights (.pt)")
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--device", type=str, default="0", help="CUDA device, e.g. 0 or 0,1 or cpu")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--project", type=str, default="runs/train")
    parser.add_argument("--name", type=str, default="vehicle_flow_yolov13_lite_single")
    parser.add_argument("--patience", type=int, default=25, help="Early stopping patience")
    parser.add_argument("--cache", action="store_true", help="Cache images for faster training")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def resolve_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (root / path).resolve()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parent
    yolo_lite_dir = root / "yolov13-lite"

    if not yolo_lite_dir.exists():
        raise FileNotFoundError(f"Cannot find directory: {yolo_lite_dir}")

    # Ensure importing local modified ultralytics from yolov13-lite
    sys.path.insert(0, str(yolo_lite_dir))
    from ultralytics import YOLO  # pylint: disable=import-error,import-outside-toplevel

    model_path = resolve_path(root, args.model)
    data_path = ensure_single_class_dataset(resolve_path(root, args.data))
    project_path = resolve_path(root, args.project)

    model = YOLO(str(model_path))
    if args.weights:
        weights_path = resolve_path(root, args.weights)
        model = model.load(str(weights_path))

    # [训练参数修改入口] 训练轮数、分辨率、batch、设备等都在这里传给 train()
    model.train(
        data=str(data_path),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        project=str(project_path),
        name=args.name,
        patience=args.patience,
        resume=args.resume,
        cache=args.cache,
        single_cls=True,
    )


if __name__ == "__main__":
    main()


'''
python ./train_yolov13_lite_eucb.py \
  --data ./datasets/vehicle_flow/vehicle_flow.yaml \
  --epochs 80 \
  --imgsz 960 \
  --batch 24 \
  --device 0 \
  --project ./runs/train \
  --name vehicle_flow_yolov13_lite_single
'''
