from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.single_class_dataset import ensure_single_class_dataset


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parent
    default_weights = root / "yolov12n.pt"
    default_model = (
        default_weights
        if default_weights.exists()
        else root / "yolov12" / "ultralytics" / "cfg" / "models" / "v12" / "yolov12.yaml"
    )

    parser = argparse.ArgumentParser(description="Train YOLOv12 for vehicle-flow detection")
    parser.add_argument("--data", type=str, required=True, help="Dataset yaml path")
    parser.add_argument("--model", type=str, default=str(default_model), help="Model yaml or .pt path")
    parser.add_argument("--weights", type=str, default="", help="Optional pretrained weights (.pt)")
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--device", type=str, default="0", help="CUDA device, e.g. 0 or 0,1 or cpu")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--project", type=str, default="runs/train")
    parser.add_argument("--name", type=str, default="vehicle_flow_yolov12_single")
    parser.add_argument("--patience", type=int, default=25, help="Early stopping patience")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--cache", action="store_true", help="Cache images for faster training")
    parser.add_argument("--pretrained", action="store_true", help="Let Ultralytics use pretrained weights when supported")
    return parser.parse_args()


def resolve_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (root / path).resolve()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parent
    yolo_dir = root / "yolov12"

    if not yolo_dir.exists():
        raise FileNotFoundError(f"Cannot find directory: {yolo_dir}")

    # Ensure importing the local YOLOv12 codebase used for the comparison experiment.
    sys.path.insert(0, str(yolo_dir))
    from ultralytics import YOLO  # pylint: disable=import-error,import-outside-toplevel

    model_path = resolve_path(root, args.model)
    data_path = ensure_single_class_dataset(resolve_path(root, args.data))
    project_path = resolve_path(root, args.project)

    if not model_path.exists():
        raise FileNotFoundError(f"Cannot find model config or weights: {model_path}")
    model = YOLO(str(model_path))
    if args.weights:
        weights_path = resolve_path(root, args.weights)
        if not weights_path.exists():
            raise FileNotFoundError(f"Cannot find pretrained weights: {weights_path}")
        model = model.load(str(weights_path))

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
        pretrained=args.pretrained,
    )


if __name__ == "__main__":
    main()


'''
python ./train_yolov12.py \
  --data ./datasets/vehicle_flow/vehicle_flow.yaml \
  --epochs 80 \
  --imgsz 960 \
  --batch 24 \
  --device 0 \
  --project ./runs/train \
  --name vehicle_flow_yolov12_single
'''
