from __future__ import annotations

import argparse
import random
import shutil
from pathlib import Path


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Randomly sample a YOLO-format dataset.")
    parser.add_argument("--src", type=str, required=True, help="Source dataset root.")
    parser.add_argument("--dst", type=str, required=True, help="Output sampled dataset root.")
    parser.add_argument("--count", type=int, default=20000, help="Total number of images to sample.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument(
        "--mode",
        type=str,
        default="preserve",
        choices=["preserve", "train-only"],
        help="preserve: keep train/val proportion. train-only: only sample from images/train.",
    )
    parser.add_argument(
        "--copy-empty-labels",
        action="store_true",
        help="Create empty label txt when source label file is missing.",
    )
    return parser.parse_args()


def resolve(path_str: str) -> Path:
    return Path(path_str).expanduser().resolve()


def list_images(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(path for path in directory.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES)


def corresponding_label(dataset_root: Path, image_path: Path) -> Path:
    relative = image_path.relative_to(dataset_root / "images")
    return (dataset_root / "labels" / relative).with_suffix(".txt")


def copy_one(dataset_root: Path, image_path: Path, output_root: Path, copy_empty_labels: bool) -> None:
    relative = image_path.relative_to(dataset_root / "images")
    dst_image = output_root / "images" / relative
    dst_label = (output_root / "labels" / relative).with_suffix(".txt")
    src_label = corresponding_label(dataset_root, image_path)

    dst_image.parent.mkdir(parents=True, exist_ok=True)
    dst_label.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(image_path, dst_image)
    if src_label.exists():
        shutil.copy2(src_label, dst_label)
    elif copy_empty_labels:
        dst_label.write_text("", encoding="utf-8")
    else:
        raise FileNotFoundError(f"Missing label file for image: {image_path}")


def sample_preserve(train_images: list[Path], val_images: list[Path], total_count: int) -> tuple[list[Path], list[Path]]:
    available_total = len(train_images) + len(val_images)
    if total_count > available_total:
        raise ValueError(f"Requested {total_count} images, but only {available_total} are available.")

    if available_total == 0:
        return [], []

    train_count = round(total_count * len(train_images) / available_total)
    train_count = min(train_count, len(train_images))
    val_count = min(total_count - train_count, len(val_images))

    # If one split is exhausted, give the remainder to the other split.
    remainder = total_count - train_count - val_count
    if remainder > 0:
        extra_train = min(remainder, len(train_images) - train_count)
        train_count += extra_train
        remainder -= extra_train
    if remainder > 0:
        extra_val = min(remainder, len(val_images) - val_count)
        val_count += extra_val

    return train_images[:train_count], val_images[:val_count]


def main() -> None:
    args = parse_args()
    random.seed(args.seed)

    src_root = resolve(args.src)
    dst_root = resolve(args.dst)

    train_dir = src_root / "images" / "train"
    val_dir = src_root / "images" / "val"

    train_images = list_images(train_dir)
    val_images = list_images(val_dir)

    if args.mode == "train-only":
        if args.count > len(train_images):
            raise ValueError(f"Requested {args.count} images, but train split only has {len(train_images)}.")
        random.shuffle(train_images)
        chosen_train = train_images[: args.count]
        chosen_val: list[Path] = []
    else:
        random.shuffle(train_images)
        random.shuffle(val_images)
        chosen_train, chosen_val = sample_preserve(train_images, val_images, args.count)

    if dst_root.exists():
        raise FileExistsError(f"Output directory already exists: {dst_root}")

    for image_path in chosen_train:
        copy_one(src_root, image_path, dst_root, args.copy_empty_labels)
    for image_path in chosen_val:
        copy_one(src_root, image_path, dst_root, args.copy_empty_labels)

    train_count = len(chosen_train)
    val_count = len(chosen_val)
    names_path = src_root / "vehicle_flow.yaml"
    if names_path.exists():
        shutil.copy2(names_path, dst_root / "vehicle_flow.yaml")

    print(f"Sampled dataset created: {dst_root}")
    print(f"train: {train_count}")
    print(f"val: {val_count}")
    print(f"total: {train_count + val_count}")


if __name__ == "__main__":
    main()
