import argparse
import json
import random
from pathlib import Path


ALLOWED_EXT = {".npy", ".npz"}
DEFAULT_LABEL_MAP = {
    "normal": 0,
    "fall": 1,
    "punch": 2,
    "fight": 2,
    "wave": 3,
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build train/val jsonl manifests from folder-based pose sequence dataset."
    )
    parser.add_argument(
        "--dataset-root",
        required=True,
        help="Root dir with class subfolders, e.g. normal/fall/punch/wave.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory for train.jsonl, val.jsonl and label_meta.json.",
    )
    parser.add_argument(
        "--val-ratio",
        type=float,
        default=0.2,
        help="Validation split ratio in [0,1).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible split.",
    )
    return parser.parse_args()


def collect_samples(dataset_root):
    samples = []
    for class_dir in sorted(dataset_root.iterdir()):
        if not class_dir.is_dir():
            continue
        class_name = class_dir.name.strip().lower()
        if class_name not in DEFAULT_LABEL_MAP:
            continue
        label = DEFAULT_LABEL_MAP[class_name]
        for file_path in class_dir.rglob("*"):
            if not file_path.is_file() or file_path.suffix.lower() not in ALLOWED_EXT:
                continue
            samples.append(
                {
                    "sequence_path": str(file_path.resolve()),
                    "label": int(label),
                    "label_name": class_name,
                }
            )
    return samples


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main():
    args = parse_args()
    dataset_root = Path(args.dataset_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not dataset_root.exists():
        raise FileNotFoundError(f"dataset root not found: {dataset_root}")
    if not (0.0 <= args.val_ratio < 1.0):
        raise ValueError("--val-ratio must be in [0,1)")

    samples = collect_samples(dataset_root)
    if not samples:
        raise RuntimeError(
            "No sequence files found. Expected class subfolders with .npy/.npz files."
        )

    random.seed(args.seed)
    random.shuffle(samples)
    split_at = int(len(samples) * (1.0 - args.val_ratio))
    train_rows = samples[:split_at]
    val_rows = samples[split_at:]

    train_path = output_dir / "train.jsonl"
    val_path = output_dir / "val.jsonl"
    meta_path = output_dir / "label_meta.json"

    write_jsonl(train_path, train_rows)
    write_jsonl(val_path, val_rows)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "label_map": DEFAULT_LABEL_MAP,
                "label_names_for_infer": ["normal", "fall", "punch", "wave"],
                "train_samples": len(train_rows),
                "val_samples": len(val_rows),
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"train manifest: {train_path}")
    print(f"val manifest:   {val_path}")
    print(f"meta:           {meta_path}")
    print(f"samples: train={len(train_rows)}, val={len(val_rows)}")


if __name__ == "__main__":
    main()
