from __future__ import annotations

import os
import shutil
from pathlib import Path


VEHICLE_CLASS_ID = 0
VEHICLE_CLASS_NAME = "vehicle"


def ensure_single_class_dataset(source_yaml: Path, output_root: Path | None = None) -> Path:
    """Create a generated single-class vehicle dataset and return its yaml path."""
    source_yaml = source_yaml.resolve()
    if source_yaml.parent.name.endswith("_single"):
        has_generated_data = all(
            path.exists()
            for path in (
                source_yaml.parent / "images" / "train",
                source_yaml.parent / "images" / "val",
                source_yaml.parent / "labels" / "train",
                source_yaml.parent / "labels" / "val",
            )
        )
        if has_generated_data:
            _write_single_class_yaml(source_yaml, source_yaml.parent)
            return source_yaml
        raw_root = source_yaml.parent.with_name(source_yaml.parent.name.removesuffix("_single"))
        raw_yaml = raw_root / source_yaml.name
        if raw_yaml.exists():
            output_root = output_root or source_yaml.parent
            source_yaml = raw_yaml.resolve()

    source_data = _read_simple_yaml(source_yaml)
    source_root = _resolve_dataset_root(source_yaml, source_data)
    output_root = output_root or (source_yaml.parent.parent / f"{source_yaml.parent.name}_single")
    output_root = output_root.resolve()

    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "images").mkdir(exist_ok=True)
    (output_root / "labels").mkdir(exist_ok=True)

    split_entries: dict[str, str] = {}
    for split_name in ("train", "val", "test"):
        split_value = source_data.get(split_name)
        if not split_value:
            continue

        source_images = _resolve_split_path(source_root, split_value)
        source_labels = _label_dir_for_split(source_root, source_images, split_name)
        target_images = output_root / "images" / split_name
        target_labels = output_root / "labels" / split_name

        _ensure_image_link(source_images, target_images)
        _rewrite_labels_as_vehicle(source_labels, target_labels)
        split_entries[split_name] = f"images/{split_name}"

    yaml_path = output_root / "vehicle_flow.yaml"
    _write_single_class_yaml(yaml_path, output_root, split_entries)
    return yaml_path


def _read_simple_yaml(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("'\"")
    return data


def _resolve_dataset_root(yaml_path: Path, data: dict[str, str]) -> Path:
    raw_path = data.get("path")
    if not raw_path:
        return yaml_path.parent
    dataset_root = Path(raw_path)
    return dataset_root if dataset_root.is_absolute() else (yaml_path.parent / dataset_root).resolve()


def _resolve_split_path(dataset_root: Path, split_value: str) -> Path:
    split_path = Path(split_value)
    return split_path if split_path.is_absolute() else (dataset_root / split_path).resolve()


def _label_dir_for_split(dataset_root: Path, image_dir: Path, split_name: str) -> Path:
    parts = list(image_dir.parts)
    if "images" in parts:
        parts[parts.index("images")] = "labels"
        return Path(*parts)
    return dataset_root / "labels" / split_name


def _ensure_image_link(source: Path, target: Path) -> None:
    if target.exists() or target.is_symlink():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        relative_source = os.path.relpath(source, start=target.parent)
        target.symlink_to(relative_source, target_is_directory=True)
    except OSError:
        # Windows without symlink privileges can still use this script for small smoke datasets.
        shutil.copytree(source, target)


def _rewrite_labels_as_vehicle(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for source_file in source.rglob("*.txt"):
        target_file = target / source_file.relative_to(source)
        target_file.parent.mkdir(parents=True, exist_ok=True)
        rewritten_lines = []
        for raw_line in source_file.read_text(encoding="utf-8").splitlines():
            parts = raw_line.split()
            if len(parts) < 5:
                continue
            rewritten_lines.append(" ".join([str(VEHICLE_CLASS_ID), *parts[1:5]]))
        target_file.write_text("\n".join(rewritten_lines) + ("\n" if rewritten_lines else ""), encoding="utf-8")


def _write_single_class_yaml(
    yaml_path: Path,
    dataset_root: Path,
    split_entries: dict[str, str] | None = None,
) -> None:
    split_entries = split_entries or {
        "train": "images/train",
        "val": "images/val",
    }
    yaml_lines = [f"path: {dataset_root.as_posix()}"]
    for split_name in ("train", "val", "test"):
        if split_name in split_entries:
            yaml_lines.append(f"{split_name}: {split_entries[split_name]}")
    yaml_lines.extend(["", "names:", f"  {VEHICLE_CLASS_ID}: {VEHICLE_CLASS_NAME}", ""])
    yaml_path.write_text("\n".join(yaml_lines), encoding="utf-8")
