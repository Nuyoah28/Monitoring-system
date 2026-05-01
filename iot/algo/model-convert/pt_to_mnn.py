from __future__ import annotations

import argparse
from pathlib import Path

from convert_onnx_to_mnn import main as convert_onnx_to_mnn_main
from export_pt_to_onnx import main as export_pt_to_onnx_main


SCRIPT_DIR = Path(__file__).resolve().parent


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
    argv = [
        "export_pt_to_onnx.py",
        "--weights",
        args.weights,
        "--imgsz",
        str(args.imgsz),
        "--device",
        args.device,
        "--opset",
        str(args.opset),
        "--batch",
        str(args.batch),
    ]
    if args.onnx_output:
        argv.extend(["--output", args.onnx_output])
    if args.ultralytics_dir:
        argv.extend(["--ultralytics-dir", args.ultralytics_dir])
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

    if args.onnx_output:
        path = Path(args.onnx_output)
        return path if path.is_absolute() else (Path.cwd() / path).resolve()

    weights_path = Path(args.weights)
    if not weights_path.is_absolute():
        weights_path = (Path.cwd() / weights_path).resolve()
    return weights_path.with_suffix(".onnx")


def run_mnn_convert(args: argparse.Namespace, onnx_path: Path) -> None:
    argv = [
        "convert_onnx_to_mnn.py",
        "--onnx",
        str(onnx_path),
        "--biz-code",
        args.biz_code,
    ]
    if args.mnn_output:
        argv.extend(["--output", args.mnn_output])
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
