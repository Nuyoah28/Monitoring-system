from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]


def resolve_input_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path

    candidates = [
        (Path.cwd() / path).resolve(),
        (SCRIPT_DIR / path).resolve(),
        (REPO_ROOT / path).resolve(),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def resolve_output_path(value: str | None, default_path: Path) -> Path:
    if not value:
        return default_path

    path = Path(value)
    if not path.suffix:
        path = path.with_suffix(".mnn")
    if path.is_absolute():
        return path
    return (Path.cwd() / path).resolve()


def find_mnnconvert(explicit_path: str | None) -> Path:
    if explicit_path:
        candidate = resolve_input_path(explicit_path)
        if candidate.exists():
            return candidate
        raise FileNotFoundError(f"Cannot find MNNConvert: {candidate}")

    candidates = [
        REPO_ROOT / "iot" / "MNN" / "build" / "MNNConvert.exe",
        REPO_ROOT / "iot" / "MNN" / "build" / "MNNConvert",
        REPO_ROOT / "iot" / "MNN" / "build" / "Release" / "MNNConvert.exe",
        REPO_ROOT / "iot" / "MNN" / "build" / "Release" / "MNNConvert",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    joined = "\n".join(str(path) for path in candidates)
    raise FileNotFoundError(f"Cannot find MNNConvert. Checked:\n{joined}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert an ONNX model to MNN.")
    parser.add_argument("--onnx", required=True, help="Path to the input .onnx file.")
    parser.add_argument("--output", help="Output .mnn path. Defaults next to the ONNX model.")
    parser.add_argument("--mnnconvert", help="Optional explicit path to the MNNConvert executable.")
    parser.add_argument("--biz-code", default="MNN", help="Value passed to --bizCode.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    onnx_path = resolve_input_path(args.onnx)
    if not onnx_path.exists():
        raise FileNotFoundError(f"Cannot find ONNX model: {onnx_path}")

    output_path = resolve_output_path(args.output, onnx_path.with_suffix(".mnn"))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    mnnconvert_path = find_mnnconvert(args.mnnconvert)
    command = [
        str(mnnconvert_path),
        "-f",
        "ONNX",
        "--modelFile",
        str(onnx_path),
        "--MNNModel",
        str(output_path),
        "--bizCode",
        args.biz_code,
    ]

    print("[run]", " ".join(command))
    subprocess.run(command, check=True)
    print(f"[ok] mnn exported: {output_path}")


if __name__ == "__main__":
    main()
