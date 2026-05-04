from __future__ import annotations

import argparse
from pathlib import Path

from convert_onnx_to_mnn import main as convert_onnx_to_mnn_main
from export_pt_to_onnx import main as export_pt_to_onnx_main


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent

ULTRALYTICS_BY_STEM = {
    "yolov8": "yolov13-lite",
    "yolov12": "yolov12",
    "yolov13": "yolov13",
    "yolov13-eucb": "yolov13-lite",
}


def default_ultralytics_dir(weights_path: Path) -> Path:
    return PROJECT_DIR / ULTRALYTICS_BY_STEM.get(weights_path.stem, "yolov13-lite")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert a .pt model to .onnx and then to .mnn.")
    parser.add_argument("--weights", required=True, help="Path to the input .pt model.")
    parser.add_argument("--onnx-output", help="Optional output .onnx path.")
    parser.add_argument("--mnn-output", help="Optional output .mnn path.")
    parser.add_argument("--imgsz", type=int, default=640, help="Inference image size.")
    parser.add_argument("--device", default="cpu", help="Export device, e.g. cpu or 0.")
    parser.add_argument("--opset", type=int, default=12, help="ONNX opset version.")
    parser.add_argument("--batch", type=int, default=1, help="Static batch size for export.")
    parser.add_argument("--ultralytics-dir", help="Local ultralytics code path.")
    parser.add_argument("--mnnconvert", help="Optional explicit path to the MNNConvert executable.")
    parser.add_argument("--dynamic", action="store_true", help="Enable dynamic input shape export.")
    parser.add_argument("--simplify", action="store_true", help="Simplify ONNX graph after export.")
    parser.add_argument("--half", action="store_true", help="Export with FP16 when supported.")
    parser.add_argument("--nms", action="store_true", help="Export model with NMS.")
    parser.add_argument("--biz-code", default="MNN", help="Value passed to --bizCode.")
    return parser.parse_args()


def run_export(args: argparse.Namespace) -> Path:
    weights_path = Path(args.weights)
    if not weights_path.is_absolute():
        candidates = [
            (Path.cwd() / weights_path).resolve(),
            (PROJECT_DIR / "models" / "pt" / weights_path).resolve(),
        ]
        weights_path = next((candidate for candidate in candidates if candidate.exists()), candidates[0])

    onnx_output = args.onnx_output
    if not onnx_output:
        onnx_output = str(PROJECT_DIR / "models" / "onnx" / f"{weights_path.stem}.onnx")

    argv = [
        "export_pt_to_onnx.py",
        "--weights",
        str(weights_path),
        "--imgsz",
        str(args.imgsz),
        "--device",
        args.device,
        "--opset",
        str(args.opset),
        "--batch",
        str(args.batch),
        "--output",
        onnx_output,
    ]
    argv.extend(["--ultralytics-dir", args.ultralytics_dir or str(default_ultralytics_dir(weights_path))])
    if args.dynamic:
        argv.append("--dynamic")
    if args.simplify:
        argv.append("--simplify")
    if args.half:
        argv.append("--half")
    if args.nms:
        argv.append("--nms")

    import sys

    previous_argv = sys.argv
    try:
        sys.argv = argv
        export_pt_to_onnx_main()
    finally:
        sys.argv = previous_argv

    path = Path(onnx_output)
    return path if path.is_absolute() else (Path.cwd() / path).resolve()


def run_mnn_convert(args: argparse.Namespace, onnx_path: Path) -> None:
    mnn_output = args.mnn_output
    if not mnn_output:
        mnn_output = str(PROJECT_DIR / "models" / "mnn" / f"{onnx_path.stem}.mnn")

    argv = [
        "convert_onnx_to_mnn.py",
        "--onnx",
        str(onnx_path),
        "--biz-code",
        args.biz_code,
        "--output",
        mnn_output,
    ]
    if args.mnnconvert:
        argv.extend(["--mnnconvert", args.mnnconvert])

    import sys

    previous_argv = sys.argv
    try:
        sys.argv = argv
        convert_onnx_to_mnn_main()
    finally:
        sys.argv = previous_argv


def main() -> None:
    args = parse_args()
    onnx_path = run_export(args)
    run_mnn_convert(args, onnx_path)


if __name__ == "__main__":
    main()
