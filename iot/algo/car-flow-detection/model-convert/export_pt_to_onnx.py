from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DEFAULT_ULTRALYTICS_DIR = PROJECT_DIR / "yolov13-lite"


def resolve_input_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path

    candidates = [
        (Path.cwd() / path).resolve(),
        (PROJECT_DIR / path).resolve(),
        (PROJECT_DIR / "models" / "pt" / path).resolve(),
        (SCRIPT_DIR / path).resolve(),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def resolve_output_path(value: str | None, default_suffix: str) -> Path | None:
    if not value:
        return None

    path = Path(value)
    if not path.suffix:
        path = path.with_suffix(default_suffix)
    if path.is_absolute():
        return path
    return (Path.cwd() / path).resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a YOLO .pt model to ONNX.")
    parser.add_argument("--weights", required=True, help="Path to the input .pt model.")
    parser.add_argument("--output", help="Output .onnx path. Defaults to the exporter output path.")
    parser.add_argument("--imgsz", type=int, default=640, help="Inference image size.")
    parser.add_argument("--device", default="cpu", help="Export device, e.g. cpu or 0.")
    parser.add_argument("--opset", type=int, default=12, help="ONNX opset version.")
    parser.add_argument("--batch", type=int, default=1, help="Static batch size for export.")
    parser.add_argument("--ultralytics-dir", default=str(DEFAULT_ULTRALYTICS_DIR), help="Local ultralytics code path.")
    parser.add_argument("--dynamic", action="store_true", help="Enable dynamic input shape export.")
    parser.add_argument("--simplify", action="store_true", help="Simplify ONNX graph after export.")
    parser.add_argument("--half", action="store_true", help="Export with FP16 when supported.")
    parser.add_argument("--nms", action="store_true", help="Export model with NMS.")
    return parser.parse_args()


def ensure_local_ultralytics(ultralytics_dir: Path) -> None:
    if not ultralytics_dir.exists():
        raise FileNotFoundError(f"Cannot find local ultralytics directory: {ultralytics_dir}")
    restore_sourceless_modules(ultralytics_dir)
    sys.path.insert(0, str(ultralytics_dir))


def restore_sourceless_modules(ultralytics_dir: Path) -> None:
    """Use bundled pycache files when a trimmed YOLO tree has empty source modules."""
    cache_tag = sys.implementation.cache_tag
    candidate_dirs = [
        ultralytics_dir / "ultralytics" / "nn" / "modules",
        ultralytics_dir / "ultralytics" / "models" / "yolo",
        ultralytics_dir / "ultralytics" / "utils" / "callbacks",
    ]

    for directory in candidate_dirs:
        if not directory.exists():
            continue
        pycache_dir = directory / "__pycache__"
        if not pycache_dir.exists():
            continue
        for source_path in directory.glob("*.py"):
            if source_path.name == "__init__.py":
                continue
            if source_path.stat().st_size != 0:
                continue
            cache_path = pycache_dir / f"{source_path.stem}.{cache_tag}.pyc"
            if not cache_path.exists():
                continue
            sourceless_path = source_path.with_suffix(".pyc")
            if not sourceless_path.exists() or sourceless_path.stat().st_size != cache_path.stat().st_size:
                shutil.copy2(cache_path, sourceless_path)
            source_path.rename(source_path.with_suffix(".py.empty"))


def check_opencv_runtime() -> None:
    try:
        import cv2  # noqa: F401  # pylint: disable=import-outside-toplevel,unused-import
    except ImportError as exc:
        message = str(exc)
        if "libGL.so.1" in message:
            raise RuntimeError(
                "OpenCV cannot load libGL.so.1 in this Docker environment.\n"
                "Fix it inside the container with:\n"
                "  apt-get update && apt-get install -y libgl1 libglib2.0-0\n"
                "Then rerun the conversion command."
            ) from exc
        raise


def main() -> None:
    args = parse_args()
    weights_path = resolve_input_path(args.weights)
    ultralytics_dir = resolve_input_path(args.ultralytics_dir)
    output_path = resolve_output_path(args.output, ".onnx")

    if not weights_path.exists():
        raise FileNotFoundError(f"Cannot find weights file: {weights_path}")

    ensure_local_ultralytics(ultralytics_dir)
    check_opencv_runtime()
    from ultralytics import YOLO  # pylint: disable=import-error,import-outside-toplevel

    model = YOLO(str(weights_path))
    exported = model.export(
        format="onnx",
        imgsz=args.imgsz,
        device=args.device,
        opset=args.opset,
        batch=args.batch,
        dynamic=args.dynamic,
        simplify=args.simplify,
        half=args.half,
        nms=args.nms,
        verbose=False,
    )

    exported_path = Path(exported).resolve()
    final_path = exported_path
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if exported_path != output_path:
            shutil.move(str(exported_path), str(output_path))
        final_path = output_path

    print(f"[ok] onnx exported: {final_path}")


if __name__ == "__main__":
    main()
