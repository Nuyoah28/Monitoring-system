from __future__ import annotations

import argparse
import os
import platform
import subprocess
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent


def find_repo_root() -> Path:
    for parent in [PROJECT_DIR, *PROJECT_DIR.parents]:
        if (parent / "iot").exists() or (parent / "MNN").exists() or (parent / "car-flow-detection").exists():
            return parent
    return PROJECT_DIR


REPO_ROOT = find_repo_root()


def resolve_input_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path

    candidates = [
        (Path.cwd() / path).resolve(),
        (PROJECT_DIR / path).resolve(),
        (PROJECT_DIR / "models" / "onnx" / path).resolve(),
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
            if os.name == "nt" and candidate.suffix.lower() != ".exe":
                raise OSError(
                    f"MNNConvert is not a Windows executable: {candidate}\n"
                    "On Windows, please pass a compiled MNNConvert.exe with --mnnconvert, "
                    "or run this conversion on Linux."
                )
            return candidate
        raise FileNotFoundError(f"Cannot find MNNConvert: {candidate}")

    if os.name == "nt":
        candidates = [
            PROJECT_DIR / "MNN" / "build" / "MNNConvert.exe",
            PROJECT_DIR / "MNN" / "build" / "Release" / "MNNConvert.exe",
            PROJECT_DIR / "MNN" / "build_x86_64" / "MNNConvert.exe",
            PROJECT_DIR / "MNN" / "build_x86_64" / "Release" / "MNNConvert.exe",
            REPO_ROOT / "MNN" / "build_x86_64" / "MNNConvert.exe",
            REPO_ROOT / "MNN" / "build_x86_64" / "Release" / "MNNConvert.exe",
            REPO_ROOT / "MNN" / "build" / "MNNConvert.exe",
            REPO_ROOT / "MNN" / "build" / "Release" / "MNNConvert.exe",
            REPO_ROOT / "iot" / "MNN" / "build" / "MNNConvert.exe",
            REPO_ROOT / "iot" / "MNN" / "build" / "Release" / "MNNConvert.exe",
        ]
        incompatible_candidates = [
            PROJECT_DIR / "MNN" / "build" / "MNNConvert",
            PROJECT_DIR / "MNN" / "build" / "Release" / "MNNConvert",
            REPO_ROOT / "MNN" / "build" / "MNNConvert",
            REPO_ROOT / "MNN" / "build" / "Release" / "MNNConvert",
            REPO_ROOT / "iot" / "MNN" / "build" / "MNNConvert",
            REPO_ROOT / "iot" / "MNN" / "build" / "Release" / "MNNConvert",
        ]
    else:
        candidates = [
            PROJECT_DIR / "MNN" / "build_x86_64" / "MNNConvert",
            PROJECT_DIR / "MNN" / "build_x86_64" / "MNNConvert.exe",
            PROJECT_DIR / "MNN" / "build_x86_64" / "Release" / "MNNConvert",
            PROJECT_DIR / "MNN" / "build_x86_64" / "Release" / "MNNConvert.exe",
            REPO_ROOT / "MNN" / "build_x86_64" / "MNNConvert",
            REPO_ROOT / "MNN" / "build_x86_64" / "MNNConvert.exe",
            REPO_ROOT / "MNN" / "build_x86_64" / "Release" / "MNNConvert",
            REPO_ROOT / "MNN" / "build_x86_64" / "Release" / "MNNConvert.exe",
            PROJECT_DIR / "MNN" / "build" / "MNNConvert",
            PROJECT_DIR / "MNN" / "build" / "MNNConvert.exe",
            PROJECT_DIR / "MNN" / "build" / "Release" / "MNNConvert",
            PROJECT_DIR / "MNN" / "build" / "Release" / "MNNConvert.exe",
            REPO_ROOT / "MNN" / "build" / "MNNConvert",
            REPO_ROOT / "MNN" / "build" / "MNNConvert.exe",
            REPO_ROOT / "MNN" / "build" / "Release" / "MNNConvert",
            REPO_ROOT / "MNN" / "build" / "Release" / "MNNConvert.exe",
            REPO_ROOT / "iot" / "MNN" / "build" / "MNNConvert",
            REPO_ROOT / "iot" / "MNN" / "build" / "MNNConvert.exe",
            REPO_ROOT / "iot" / "MNN" / "build" / "Release" / "MNNConvert",
            REPO_ROOT / "iot" / "MNN" / "build" / "Release" / "MNNConvert.exe",
        ]
        incompatible_candidates = []

    for candidate in candidates:
        if candidate.exists():
            return candidate

    joined = "\n".join(str(path) for path in candidates)
    incompatible = "\n".join(str(path) for path in incompatible_candidates if path.exists())
    if incompatible:
        raise FileNotFoundError(
            "Cannot find Windows MNNConvert.exe. Found non-Windows MNNConvert files:\n"
            f"{incompatible}\n\n"
            "Please build MNNConvert.exe on Windows, pass it with --mnnconvert, "
            "or run the MNN conversion on Linux.\n"
            f"Checked:\n{joined}"
        )
    raise FileNotFoundError(f"Cannot find MNNConvert. Checked:\n{joined}")


def detect_elf_arch(path: Path) -> str | None:
    with path.open("rb") as file:
        header = file.read(20)
    if len(header) < 20 or header[:4] != b"\x7fELF":
        return None
    endian = "little" if header[5] == 1 else "big"
    machine = int.from_bytes(header[18:20], endian)
    return {
        3: "x86",
        40: "arm",
        62: "x86_64",
        183: "aarch64",
    }.get(machine, f"elf_machine_{machine}")


def normalize_host_arch(value: str) -> str:
    value = value.lower()
    if value in {"amd64", "x86_64"}:
        return "x86_64"
    if value in {"arm64", "aarch64"}:
        return "aarch64"
    return value


def validate_mnnconvert_arch(path: Path) -> None:
    binary_arch = detect_elf_arch(path)
    if binary_arch is None:
        return
    host_arch = normalize_host_arch(platform.machine())
    if binary_arch != host_arch:
        raise RuntimeError(
            f"MNNConvert architecture mismatch: binary={binary_arch}, host={host_arch}, path={path}\n"
            "Please use an MNNConvert built for the current container architecture, "
            "or run the container with a matching architecture."
        )


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
    validate_mnnconvert_arch(mnnconvert_path)
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
