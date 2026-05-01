from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train YOLOv8 for parking-space or vehicle detection")
    parser.add_argument("--data", type=str, required=True, help="Dataset yaml path")
    parser.add_argument(
        "--variant",
        type=str,
        default="n",
        choices=["n", "s", "m", "l", "x"],
        help="YOLOv8 model scale: n/s/m/l/x",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="",
        help="Optional model yaml or .pt path. If empty, use local yolov8{variant}.yaml",
    )
    parser.add_argument("--weights", type=str, default="", help="Optional pretrained weights (.pt)")
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--device", type=str, default="0", help="CUDA device, e.g. 0 or 0,1 or cpu")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--project", type=str, default="runs/train")
    parser.add_argument("--name", type=str, default="yolov8_train")
    parser.add_argument("--patience", type=int, default=50, help="Early stopping patience")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--cache", action="store_true", help="Cache images for faster training")
    parser.add_argument("--single-cls", action="store_true", help="Treat dataset as single-class")
    return parser.parse_args()


def resolve_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (root / path).resolve()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parent
    ultralytics_dir = root / "yolov13-lite"

    if not ultralytics_dir.exists():
        raise FileNotFoundError(f"Cannot find directory: {ultralytics_dir}")

    # Reuse the local Ultralytics fork so training and later validation stay in the same environment.
    sys.path.insert(0, str(ultralytics_dir))
    from ultralytics import YOLO  # pylint: disable=import-error,import-outside-toplevel

    default_model = ultralytics_dir / "ultralytics" / "cfg" / "models" / "v8" / f"yolov8{args.variant}.yaml"
    model_path = resolve_path(root, args.model) if args.model else default_model.resolve()
    data_path = resolve_path(root, args.data)

    model = YOLO(str(model_path))
    if args.weights:
        weights_path = resolve_path(root, args.weights)
        model = model.load(str(weights_path))

    model.train(
        data=str(data_path),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        project=args.project,
        name=args.name,
        patience=args.patience,
        resume=args.resume,
        cache=args.cache,
        single_cls=args.single_cls,
    )


if __name__ == "__main__":
    main()


'''
python .\parking_space_occupancy_detection\train_yolov8.py `
  --data ..\img\PKLot\data.yaml `
  --epochs 90 `
  --imgsz 640 `
  --batch 16 `
  --device 0 `
  --project .\parking_space_occupancy_detection\runs_v8\train `
  --name yolov8_original_pklot
'''