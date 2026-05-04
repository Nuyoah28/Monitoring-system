from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Single-model worker for compare_models.py")
    parser.add_argument("--model-name", type=str, required=True)
    parser.add_argument("--ultralytics-dir", type=str, required=True)
    parser.add_argument("--model-path", type=str, required=True)
    parser.add_argument("--data", type=str, required=True)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", type=str, default="0")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--split", type=str, default="val")
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--iou", type=float, default=0.7)
    parser.add_argument("--max-det", type=int, default=300)
    parser.add_argument("--benchmark-samples", type=int, default=100)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--half", action="store_true")
    parser.add_argument("--project", type=str, required=True)
    parser.add_argument("--run-name", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    return parser.parse_args()


def resolve(path: str) -> Path:
    return Path(path).resolve()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def collect_split_images(dataset_yaml: Path, split_name: str) -> list[Path]:
    import yaml

    with dataset_yaml.open("r", encoding="utf-8") as file:
        payload = yaml.safe_load(file)

    dataset_root = dataset_yaml.parent
    if payload.get("path"):
        path_value = Path(payload["path"])
        dataset_root = path_value if path_value.is_absolute() else (dataset_yaml.parent / path_value).resolve()

    split_value = payload.get(split_name)
    if split_value is None:
        return []

    if isinstance(split_value, list):
        candidates = split_value
    else:
        candidates = [split_value]

    images: list[Path] = []
    for candidate in candidates:
        candidate_path = Path(candidate)
        if not candidate_path.is_absolute():
            candidate_path = (dataset_root / candidate_path).resolve()

        if candidate_path.is_dir():
            images.extend(
                sorted(path for path in candidate_path.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES)
            )
            continue

        if candidate_path.is_file() and candidate_path.suffix.lower() == ".txt":
            for line in candidate_path.read_text(encoding="utf-8").splitlines():
                raw = line.strip()
                if not raw:
                    continue
                image_path = Path(raw)
                if not image_path.is_absolute():
                    image_path = (dataset_root / image_path).resolve()
                images.append(image_path)
            continue

        if candidate_path.is_file() and candidate_path.suffix.lower() in IMAGE_SUFFIXES:
            images.append(candidate_path)

    unique_images = []
    seen = set()
    for image in images:
        key = str(image)
        if key in seen:
            continue
        seen.add(key)
        unique_images.append(image)
    return unique_images


def benchmark_wall_latency(
    model: Any,
    image_paths: list[Path],
    imgsz: int,
    device: str,
    half: bool,
    conf: float,
    iou: float,
    max_det: int,
    warmup: int,
) -> dict[str, Any]:
    import torch

    if not image_paths:
        return {"latency_ms": None, "fps": None, "num_images": 0}

    benchmark_paths = image_paths
    for index in range(min(warmup, len(benchmark_paths))):
        model.predict(
            source=str(benchmark_paths[index]),
            imgsz=imgsz,
            device=device,
            half=half,
            conf=conf,
            iou=iou,
            max_det=max_det,
            classes=[0],
            verbose=False,
        )

    latencies = []
    use_cuda_sync = device != "cpu" and torch.cuda.is_available()

    for image_path in benchmark_paths:
        if use_cuda_sync:
            torch.cuda.synchronize()
        start = time.perf_counter()
        model.predict(
            source=str(image_path),
            imgsz=imgsz,
            device=device,
            half=half,
            conf=conf,
            iou=iou,
            max_det=max_det,
            classes=[0],
            verbose=False,
        )
        if use_cuda_sync:
            torch.cuda.synchronize()
        end = time.perf_counter()
        latencies.append((end - start) * 1000.0)

    latency_ms = sum(latencies) / len(latencies)
    fps = 1000.0 / latency_ms if latency_ms > 0 else None
    return {"latency_ms": latency_ms, "fps": fps, "num_images": len(latencies)}


def main() -> None:
    args = parse_args()

    ultralytics_dir = resolve(args.ultralytics_dir)
    model_path = resolve(args.model_path)
    data_path = resolve(args.data)
    output_path = resolve(args.output)
    project_dir = resolve(args.project)

    import sys

    sys.path.insert(0, str(ultralytics_dir))
    from ultralytics import YOLO  # pylint: disable=import-error,import-outside-toplevel
    from ultralytics.utils.torch_utils import (  # pylint: disable=import-error,import-outside-toplevel
        get_flops,
        get_num_gradients,
        get_num_params,
    )

    model = YOLO(str(model_path))
    val_results = model.val(
        data=str(data_path),
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        split=args.split,
        half=args.half,
        conf=args.conf,
        iou=args.iou,
        max_det=args.max_det,
        single_cls=True,
        plots=False,
        verbose=False,
        project=str(project_dir),
        name=args.run_name,
    )

    metrics_dict = val_results.results_dict
    speed_dict = dict(val_results.speed)
    total_inference_ms = (
        (speed_dict.get("preprocess", 0.0) or 0.0)
        + (speed_dict.get("inference", 0.0) or 0.0)
        + (speed_dict.get("postprocess", 0.0) or 0.0)
    )
    fps = 1000.0 / total_inference_ms if total_inference_ms > 0 else None

    image_paths = collect_split_images(data_path, args.split)
    if args.benchmark_samples > 0:
        image_paths = image_paths[: args.benchmark_samples]
    wall_benchmark = benchmark_wall_latency(
        model=model,
        image_paths=image_paths,
        imgsz=args.imgsz,
        device=args.device,
        half=args.half,
        conf=args.conf,
        iou=args.iou,
        max_det=args.max_det,
        warmup=args.warmup,
    )

    payload = {
        "status": "ok",
        "model_name": args.model_name,
        "ultralytics_dir": str(ultralytics_dir),
        "model_path": str(model_path),
        "data_path": str(data_path),
        "metrics": {
            "precision": metrics_dict.get("metrics/precision(B)"),
            "recall": metrics_dict.get("metrics/recall(B)"),
            "map50": metrics_dict.get("metrics/mAP50(B)"),
            "map75": metrics_dict.get("metrics/mAP75(B)"),
            "map50_95": metrics_dict.get("metrics/mAP50-95(B)"),
            "fitness": metrics_dict.get("fitness"),
        },
        "speed": {
            "preprocess": speed_dict.get("preprocess"),
            "inference": speed_dict.get("inference"),
            "postprocess": speed_dict.get("postprocess"),
        },
        "fps": fps,
        "wall_benchmark": wall_benchmark,
        "model_info": {
            "params": get_num_params(model.model),
            "params_m": get_num_params(model.model) / 1_000_000.0,
            "grads": get_num_gradients(model.model),
            "flops_g": get_flops(model.model, args.imgsz),
            "weights_mb": model_path.stat().st_size / (1024.0 * 1024.0),
        },
    }
    write_json(output_path, payload)


if __name__ == "__main__":
    main()
