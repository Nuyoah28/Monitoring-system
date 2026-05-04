from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

from src.single_class_dataset import ensure_single_class_dataset


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
DEFAULT_NAMES = ("vehicle",)


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Check the vehicle-flow YOLO dataset")
    parser.add_argument(
        "--data",
        type=Path,
        default=root / "datasets" / "vehicle_flow" / "vehicle_flow.yaml",
        help="Dataset yaml path",
    )
    return parser.parse_args()


def read_dataset_yaml(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def resolve_dataset_root(yaml_path: Path, data: dict[str, str]) -> Path:
    raw_path = data.get("path")
    if not raw_path:
        return yaml_path.parent

    dataset_root = Path(raw_path)
    if dataset_root.is_absolute():
        return dataset_root
    return (yaml_path.parent / dataset_root).resolve()


def resolve_split(root: Path, value: str) -> Path:
    split = Path(value)
    return split if split.is_absolute() else root / split


def video_prefix(path: Path) -> str:
    match = re.match(r"^(.*?)_img\d+$", path.stem)
    return match.group(1) if match else path.stem


def check_split(dataset_root: Path, split_name: str, image_dir: Path, label_dir: Path) -> tuple[set[str], Counter[str]]:
    image_paths = [p for p in image_dir.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
    label_paths = list(label_dir.rglob("*.txt"))
    image_stems = {p.stem for p in image_paths}
    label_stems = {p.stem for p in label_paths}

    class_counts: Counter[int] = Counter()
    stats: Counter[str] = Counter()
    prefixes = {video_prefix(p) for p in image_paths}

    for label_path in label_paths:
        lines = label_path.read_text(encoding="utf-8").splitlines()
        if not lines:
            stats["empty_labels"] += 1
        for line_no, line in enumerate(lines, start=1):
            parts = line.split()
            if len(parts) != 5:
                stats["bad_lines"] += 1
                print(f"[bad] {label_path.relative_to(dataset_root)}:{line_no} expected 5 columns")
                continue
            try:
                cls = int(parts[0])
                values = [float(v) for v in parts[1:]]
            except ValueError:
                stats["bad_lines"] += 1
                print(f"[bad] {label_path.relative_to(dataset_root)}:{line_no} non-numeric label")
                continue
            if cls < 0 or cls >= len(DEFAULT_NAMES):
                stats["bad_classes"] += 1
                print(f"[bad] {label_path.relative_to(dataset_root)}:{line_no} class {cls} out of range")
                continue
            if any(v < 0.0 or v > 1.0 for v in values):
                stats["bad_boxes"] += 1
                print(f"[bad] {label_path.relative_to(dataset_root)}:{line_no} box value out of 0..1")
                continue
            class_counts[cls] += 1

    print(f"\n[{split_name}]")
    print(f"images: {len(image_paths)}")
    print(f"labels: {len(label_paths)}")
    print(f"missing labels: {len(image_stems - label_stems)}")
    print(f"missing images: {len(label_stems - image_stems)}")
    print(f"empty label files: {stats['empty_labels']}")
    print(f"bad lines: {stats['bad_lines']}")
    print(f"bad classes: {stats['bad_classes']}")
    print(f"bad boxes: {stats['bad_boxes']}")
    for cls, name in enumerate(DEFAULT_NAMES):
        print(f"{name}: {class_counts[cls]}")

    return prefixes, stats


def main() -> None:
    args = parse_args()
    yaml_path = ensure_single_class_dataset(args.data.resolve())
    data = read_dataset_yaml(yaml_path)
    dataset_root = resolve_dataset_root(yaml_path, data)

    train_dir = resolve_split(dataset_root, data.get("train", "images/train"))
    val_dir = resolve_split(dataset_root, data.get("val", "images/val"))
    train_labels = dataset_root / "labels" / "train"
    val_labels = dataset_root / "labels" / "val"

    print(f"dataset yaml: {yaml_path}")
    print(f"dataset root: {dataset_root}")

    train_prefixes, _ = check_split(dataset_root, "train", train_dir, train_labels)
    val_prefixes, _ = check_split(dataset_root, "val", val_dir, val_labels)

    overlap = sorted(train_prefixes & val_prefixes)
    print("\n[split leakage]")
    print(f"train video prefixes: {len(train_prefixes)}")
    print(f"val video prefixes: {len(val_prefixes)}")
    print(f"overlap video prefixes: {len(overlap)}")
    if overlap:
        print("overlap samples: " + ", ".join(overlap[:20]))


if __name__ == "__main__":
    main()
