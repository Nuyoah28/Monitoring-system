from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from src.single_class_dataset import ensure_single_class_dataset


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Compare vehicle-flow detection models on the same dataset.")
    parser.add_argument(
        "--config",
        type=str,
        default=str(root / "config" / "compare_models.example.json"),
        help="Path to model compare config JSON.",
    )
    parser.add_argument("--data", type=str, required=True, help="Dataset yaml path.")
    parser.add_argument("--imgsz", type=int, default=640, help="Validation image size.")
    parser.add_argument("--batch", type=int, default=8, help="Validation batch size.")
    parser.add_argument("--device", type=str, default="0", help="CUDA device like 0 or cpu.")
    parser.add_argument("--workers", type=int, default=4, help="Validation workers.")
    parser.add_argument("--split", type=str, default="val", help="Dataset split: train/val/test.")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold.")
    parser.add_argument("--iou", type=float, default=0.7, help="NMS IoU threshold.")
    parser.add_argument("--max-det", type=int, default=300, help="Max detections per image.")
    parser.add_argument(
        "--benchmark-samples",
        type=int,
        default=100,
        help="How many validation images to use for wall-clock latency benchmark.",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=10,
        help="Warmup iterations before wall-clock latency benchmark.",
    )
    parser.add_argument("--half", action="store_true", help="Use FP16 if supported.")
    parser.add_argument("--project", type=str, default="runs/compare", help="Output project dir.")
    parser.add_argument("--name", type=str, default="vehicle_flow_model_compare", help="Output run name.")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def resolve_path(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def slugify(value: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z._-]+", "_", value.strip())
    return slug.strip("_") or "model"


def format_float(value: Any, digits: int = 4) -> str:
    if value is None:
        return "-"
    if isinstance(value, str):
        return value
    return f"{float(value):.{digits}f}"


def format_table(rows: list[dict[str, Any]]) -> str:
    headers = [
        "Model",
        "Status",
        "P",
        "R",
        "mAP50",
        "mAP75",
        "mAP50-95",
        "Infer ms",
        "FPS",
        "E2E ms",
        "E2E FPS",
        "Params M",
        "GFLOPs",
        "Weights MB",
    ]
    table_rows = []
    for row in rows:
        table_rows.append(
            [
                row.get("name", "-"),
                row.get("status", "-"),
                format_float(row.get("precision"), 4),
                format_float(row.get("recall"), 4),
                format_float(row.get("map50"), 4),
                format_float(row.get("map75"), 4),
                format_float(row.get("map50_95"), 4),
                format_float(row.get("inference_ms"), 2),
                format_float(row.get("fps"), 2),
                format_float(row.get("wall_latency_ms"), 2),
                format_float(row.get("wall_fps"), 2),
                format_float(row.get("params_m"), 2),
                format_float(row.get("flops_g"), 2),
                format_float(row.get("weights_mb"), 2),
            ]
        )

    widths = []
    for index, header in enumerate(headers):
        cell_width = max(len(str(header)), *(len(str(row[index])) for row in table_rows)) if table_rows else len(header)
        widths.append(cell_width)

    def render_line(values: list[str]) -> str:
        return " | ".join(str(value).ljust(widths[index]) for index, value in enumerate(values))

    lines = [render_line(headers), "-+-".join("-" * width for width in widths)]
    lines.extend(render_line(row) for row in table_rows)
    return "\n".join(lines)


def format_markdown(rows: list[dict[str, Any]], args: argparse.Namespace, data_path: Path) -> str:
    headers = [
        "Model",
        "Status",
        "Precision",
        "Recall",
        "mAP50",
        "mAP50-95",
        "Val infer ms/img",
        "Val FPS",
        "Wall ms/img",
        "Wall FPS",
        "Params M",
        "GFLOPs",
        "Weights MB",
    ]
    lines = [
        "# Vehicle Flow Model Compare",
        "",
        f"- Dataset: `{data_path}`",
        f"- Split: `{args.split}`",
        f"- Image size: `{args.imgsz}`",
        f"- Batch: `{args.batch}`",
        f"- Device: `{args.device}`",
        f"- Half precision: `{args.half}`",
        f"- Wall-clock benchmark samples: `{args.benchmark_samples}`",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("name", "-")),
                    str(row.get("status", "-")),
                    format_float(row.get("precision"), 4),
                    format_float(row.get("recall"), 4),
                    format_float(row.get("map50"), 4),
                    format_float(row.get("map50_95"), 4),
                    format_float(row.get("inference_ms"), 2),
                    format_float(row.get("fps"), 2),
                    format_float(row.get("wall_latency_ms"), 2),
                    format_float(row.get("wall_fps"), 2),
                    format_float(row.get("params_m"), 2),
                    format_float(row.get("flops_g"), 2),
                    format_float(row.get("weights_mb"), 2),
                ]
            )
            + " |"
        )

    successful = [row for row in rows if row.get("status") == "ok"]
    if successful:
        best_acc = max(successful, key=lambda row: row.get("map50_95") or -1)
        best_speed = max(successful, key=lambda row: row.get("wall_fps") or row.get("fps") or -1)
        lines.extend(
            [
                "",
                "## Summary",
                "",
                f"- Best accuracy by mAP50-95: `{best_acc.get('name')}` ({format_float(best_acc.get('map50_95'), 4)}).",
                f"- Best speed by wall-clock FPS: `{best_speed.get('name')}` ({format_float(best_speed.get('wall_fps') or best_speed.get('fps'), 2)} FPS).",
                "- Precision/Recall/mAP come from `model.val`; wall-clock speed is measured by running `model.predict` on validation images one by one.",
            ]
        )

    failed = [row for row in rows if row.get("status") != "ok"]
    if failed:
        lines.extend(["", "## Failed Models", ""])
        lines.extend(f"- `{row.get('name')}`: {row.get('error')}" for row in failed)

    return "\n".join(lines) + "\n"


def flatten_result(result: dict[str, Any]) -> dict[str, Any]:
    metrics = result.get("metrics", {})
    speed = result.get("speed", {})
    wall = result.get("wall_benchmark", {})
    model_info = result.get("model_info", {})

    flattened = {
        "name": result.get("model_name"),
        "status": result.get("status", "ok"),
        "ultralytics_dir": result.get("ultralytics_dir"),
        "model_path": result.get("model_path"),
        "precision": metrics.get("precision"),
        "recall": metrics.get("recall"),
        "map50": metrics.get("map50"),
        "map75": metrics.get("map75"),
        "map50_95": metrics.get("map50_95"),
        "fitness": metrics.get("fitness"),
        "preprocess_ms": speed.get("preprocess"),
        "inference_ms": speed.get("inference"),
        "postprocess_ms": speed.get("postprocess"),
        "fps": result.get("fps"),
        "wall_latency_ms": wall.get("latency_ms"),
        "wall_fps": wall.get("fps"),
        "wall_samples": wall.get("num_images"),
        "params": model_info.get("params"),
        "params_m": model_info.get("params_m"),
        "grads": model_info.get("grads"),
        "flops_g": model_info.get("flops_g"),
        "weights_mb": model_info.get("weights_mb"),
        "error": result.get("error"),
    }
    return flattened


def add_rank_fields(rows: list[dict[str, Any]]) -> None:
    successful = [row for row in rows if row.get("status") == "ok"]
    if not successful:
        return

    best_acc = max(successful, key=lambda row: row.get("map50_95") or -1)
    best_speed = max(successful, key=lambda row: row.get("wall_fps") or row.get("fps") or -1)

    best_acc_value = best_acc.get("map50_95") or 0.0
    best_speed_value = best_speed.get("wall_fps") or best_speed.get("fps") or 0.0

    for row in rows:
        if row.get("status") != "ok":
            row["map50_95_gap_to_best"] = None
            row["fps_gap_to_best"] = None
            continue
        row["map50_95_gap_to_best"] = (row.get("map50_95") or 0.0) - best_acc_value
        current_fps = row.get("wall_fps") or row.get("fps") or 0.0
        row["fps_gap_to_best"] = current_fps - best_speed_value
        row["best_accuracy_model"] = best_acc.get("name")
        row["best_speed_model"] = best_speed.get("name")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "name",
        "status",
        "precision",
        "recall",
        "map50",
        "map75",
        "map50_95",
        "fitness",
        "preprocess_ms",
        "inference_ms",
        "postprocess_ms",
        "fps",
        "wall_latency_ms",
        "wall_fps",
        "wall_samples",
        "params",
        "params_m",
        "grads",
        "flops_g",
        "weights_mb",
        "map50_95_gap_to_best",
        "fps_gap_to_best",
        "best_accuracy_model",
        "best_speed_model",
        "ultralytics_dir",
        "model_path",
        "error",
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def run_one_model(
    root: Path,
    worker_path: Path,
    run_dir: Path,
    data_path: Path,
    args: argparse.Namespace,
    spec: dict[str, Any],
) -> dict[str, Any]:
    name = spec["name"]
    safe_name = slugify(name)
    ultralytics_dir = resolve_path(root, spec["ultralytics_dir"])
    model_path = resolve_path(root, spec["model_path"])
    output_path = run_dir / "raw" / f"{safe_name}.json"
    log_path = run_dir / "logs" / f"{safe_name}.log"
    val_project = run_dir / "val_runs"

    if not ultralytics_dir.exists():
        return {
            "name": name,
            "status": "failed",
            "ultralytics_dir": str(ultralytics_dir),
            "model_path": str(model_path),
            "error": f"Ultralytics directory not found: {ultralytics_dir}",
        }

    if not model_path.exists():
        return {
            "name": name,
            "status": "failed",
            "ultralytics_dir": str(ultralytics_dir),
            "model_path": str(model_path),
            "error": f"Model weights not found: {model_path}",
        }

    command = [
        sys.executable,
        str(worker_path),
        "--model-name",
        name,
        "--ultralytics-dir",
        str(ultralytics_dir),
        "--model-path",
        str(model_path),
        "--data",
        str(data_path),
        "--imgsz",
        str(args.imgsz),
        "--batch",
        str(args.batch),
        "--device",
        args.device,
        "--workers",
        str(args.workers),
        "--split",
        args.split,
        "--conf",
        str(args.conf),
        "--iou",
        str(args.iou),
        "--max-det",
        str(args.max_det),
        "--benchmark-samples",
        str(args.benchmark_samples),
        "--warmup",
        str(args.warmup),
        "--project",
        str(val_project),
        "--run-name",
        safe_name,
        "--output",
        str(output_path),
    ]
    if args.half:
        command.append("--half")

    completed = subprocess.run(
        command,
        cwd=str(root),
        text=True,
        capture_output=True,
        check=False,
    )

    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        f"[command]\n{' '.join(command)}\n\n[stdout]\n{completed.stdout}\n\n[stderr]\n{completed.stderr}",
        encoding="utf-8",
    )

    if completed.returncode != 0:
        return {
            "name": name,
            "status": "failed",
            "ultralytics_dir": str(ultralytics_dir),
            "model_path": str(model_path),
            "error": f"Worker exited with code {completed.returncode}. See {log_path}",
        }

    if not output_path.exists():
        return {
            "name": name,
            "status": "failed",
            "ultralytics_dir": str(ultralytics_dir),
            "model_path": str(model_path),
            "error": f"Worker did not produce output JSON. See {log_path}",
        }

    result = load_json(output_path)
    result["log_path"] = str(log_path)
    return flatten_result(result)


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parent
    config_path = resolve_path(root, args.config)
    data_path = ensure_single_class_dataset(resolve_path(root, args.data))
    worker_path = root / "compare_worker.py"

    config_payload = load_json(config_path)
    models = [item for item in config_payload.get("models", []) if item.get("enabled", True)]
    if not models:
        raise ValueError(f"No enabled models found in config: {config_path}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = resolve_path(root, args.project) / f"{args.name}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for spec in models:
        row = run_one_model(root, worker_path, run_dir, data_path, args, spec)
        rows.append(row)

    add_rank_fields(rows)

    summary_payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "config_path": str(config_path),
        "data_path": str(data_path),
        "imgsz": args.imgsz,
        "batch": args.batch,
        "device": args.device,
        "split": args.split,
        "half": args.half,
        "rows": rows,
    }
    write_json(run_dir / "summary.json", summary_payload)
    write_csv(run_dir / "summary.csv", rows)
    (run_dir / "summary.txt").write_text(format_table(rows), encoding="utf-8")
    (run_dir / "summary.md").write_text(format_markdown(rows, args, data_path), encoding="utf-8")

    print(f"Comparison finished. Output dir: {run_dir}")
    print()
    print(format_table(rows))


if __name__ == "__main__":
    main()


'''
python ./compare_models.py \
  --config ./config/compare_models.example.json \
  --data ./datasets/vehicle_flow/vehicle_flow.yaml \
  --imgsz 960 \
  --batch 24 \
  --device 0 \
  --benchmark-samples 200 \
  --project ./runs/compare \
  --name vehicle_flow_model_compare
'''
