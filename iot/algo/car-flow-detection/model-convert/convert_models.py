from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DEFAULT_MODELS_DIR = PROJECT_DIR / "models"


ULTRALYTICS_BY_STEM = {
    "yolov8": "yolov13-lite",
    "yolov12": "yolov12",
    "yolov13": "yolov13",
    "yolov13-eucb": "yolov13-lite",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch convert vehicle-flow .pt models in models/pt to ONNX and MNN."
    )
    parser.add_argument(
        "--models-dir",
        default=str(DEFAULT_MODELS_DIR),
        help="Model workspace containing pt/, onnx/, and mnn/ directories.",
    )
    parser.add_argument(
        "--weights",
        nargs="*",
        help="Optional .pt names or paths. Defaults to all *.pt files under models/pt.",
    )
    parser.add_argument("--imgsz", type=int, default=960, help="Export image size.")
    parser.add_argument("--device", default="cpu", help="Export device, e.g. cpu or 0.")
    parser.add_argument("--opset", type=int, default=12, help="ONNX opset version.")
    parser.add_argument("--batch", type=int, default=1, help="Static batch size for export.")
    parser.add_argument("--mnnconvert", help="Optional explicit path to MNNConvert.")
    parser.add_argument("--dynamic", action="store_true", help="Enable dynamic input shape export.")
    parser.add_argument("--simplify", action="store_true", help="Simplify ONNX graph after export.")
    parser.add_argument("--half", action="store_true", help="Export ONNX with FP16 when supported.")
    parser.add_argument("--nms", action="store_true", help="Export ONNX with NMS.")
    parser.add_argument("--skip-onnx", action="store_true", help="Skip .pt -> .onnx export.")
    parser.add_argument("--skip-mnn", action="store_true", help="Skip .onnx -> .mnn conversion.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing ONNX/MNN files.")
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop immediately when one model fails. By default, keep converting remaining models.",
    )
    return parser.parse_args()


def resolve_models_dir(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (Path.cwd() / path).resolve()


def resolve_weight(value: str, pt_dir: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path

    candidates = [
        (Path.cwd() / path).resolve(),
        (pt_dir / path).resolve(),
        (pt_dir / path.with_suffix(".pt")).resolve() if not path.suffix else (pt_dir / path).resolve(),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def collect_weights(args: argparse.Namespace, pt_dir: Path) -> list[Path]:
    if args.weights:
        return [resolve_weight(value, pt_dir) for value in args.weights]
    return sorted(pt_dir.glob("*.pt"))


def ultralytics_dir_for(weights_path: Path) -> Path:
    stem = weights_path.stem
    dirname = ULTRALYTICS_BY_STEM.get(stem)
    if dirname is None:
        # Most custom YOLOv13-lite experiments in this project are exported with this fork.
        dirname = "yolov13-lite"
    return PROJECT_DIR / dirname


def run_command(command: list[str]) -> None:
    print("[run]", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def remove_if_overwrite(path: Path, overwrite: bool) -> None:
    if path.exists() and overwrite:
        path.unlink()


def export_onnx(args: argparse.Namespace, weights_path: Path, onnx_path: Path) -> None:
    if onnx_path.exists() and not args.overwrite:
        print(f"[skip] onnx exists: {onnx_path}", flush=True)
        return

    remove_if_overwrite(onnx_path, args.overwrite)
    ultralytics_dir = ultralytics_dir_for(weights_path)
    if not ultralytics_dir.exists():
        raise FileNotFoundError(f"Cannot find ultralytics directory for {weights_path.name}: {ultralytics_dir}")

    command = [
        sys.executable,
        str(SCRIPT_DIR / "export_pt_to_onnx.py"),
        "--weights",
        str(weights_path),
        "--output",
        str(onnx_path),
        "--imgsz",
        str(args.imgsz),
        "--device",
        args.device,
        "--opset",
        str(args.opset),
        "--batch",
        str(args.batch),
        "--ultralytics-dir",
        str(ultralytics_dir),
    ]
    if args.dynamic:
        command.append("--dynamic")
    if args.simplify:
        command.append("--simplify")
    if args.half:
        command.append("--half")
    if args.nms:
        command.append("--nms")
    run_command(command)


def convert_mnn(args: argparse.Namespace, onnx_path: Path, mnn_path: Path) -> None:
    if mnn_path.exists() and not args.overwrite:
        print(f"[skip] mnn exists: {mnn_path}", flush=True)
        return

    remove_if_overwrite(mnn_path, args.overwrite)
    if not onnx_path.exists():
        raise FileNotFoundError(f"Cannot convert missing ONNX model: {onnx_path}")

    command = [
        sys.executable,
        str(SCRIPT_DIR / "convert_onnx_to_mnn.py"),
        "--onnx",
        str(onnx_path),
        "--output",
        str(mnn_path),
    ]
    if args.mnnconvert:
        command.extend(["--mnnconvert", args.mnnconvert])
    run_command(command)


def main() -> None:
    args = parse_args()
    models_dir = resolve_models_dir(args.models_dir)
    pt_dir = models_dir / "pt"
    onnx_dir = models_dir / "onnx"
    mnn_dir = models_dir / "mnn"

    if not pt_dir.exists():
        raise FileNotFoundError(f"Cannot find pt model directory: {pt_dir}")

    onnx_dir.mkdir(parents=True, exist_ok=True)
    mnn_dir.mkdir(parents=True, exist_ok=True)

    weights_paths = collect_weights(args, pt_dir)
    if not weights_paths:
        raise FileNotFoundError(f"No .pt models found under: {pt_dir}")

    print(f"[info] models dir: {models_dir}", flush=True)
    print(f"[info] models: {', '.join(path.name for path in weights_paths)}", flush=True)

    failures: list[tuple[str, str]] = []
    for index, weights_path in enumerate(weights_paths, start=1):
        if not weights_path.exists():
            raise FileNotFoundError(f"Cannot find weights file: {weights_path}")

        stem = weights_path.stem
        onnx_path = onnx_dir / f"{stem}.onnx"
        mnn_path = mnn_dir / f"{stem}.mnn"

        print(f"\n[{index}/{len(weights_paths)}] converting {weights_path.name}", flush=True)
        try:
            if not args.skip_onnx:
                export_onnx(args, weights_path, onnx_path)
            if not args.skip_mnn:
                convert_mnn(args, onnx_path, mnn_path)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            message = f"{type(exc).__name__}: {exc}"
            failures.append((weights_path.name, message))
            print(f"[failed] {weights_path.name}: {message}", flush=True)
            if args.stop_on_error:
                raise

    if failures:
        print("\n[done-with-errors] conversion finished with failures:", flush=True)
        for model_name, message in failures:
            print(f"  - {model_name}: {message}", flush=True)
        raise SystemExit(1)

    print("\n[ok] conversion finished", flush=True)


if __name__ == "__main__":
    main()

'''
python ./model-convert/convert_models.py \
  --models-dir ./models \
  --imgsz 960 \
  --device 0 \
  --opset 12 \
  --batch 1 \
  --simplify \
  --overwrite \
  --mnnconvert /workspaces/MNN/build_x86_64/MNNConvert
'''
