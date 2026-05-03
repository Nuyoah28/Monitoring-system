"""Standalone Mamba-YOLO inference debugger.

Run this from the algorithm environment. It bypasses the full monitoring
pipeline and tests Mamba-YOLO directly on an image, a directory of images, or a
video file.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from config import RuntimeConfig as Config  # noqa: E402
from Yolov8.mamba_yolo import MambaYOLODetector  # noqa: E402


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".flv"}


def resolve_path(value: str | os.PathLike | None) -> Path | None:
    if value is None or str(value).strip() == "":
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT / path


def normalize_label(value: str) -> str:
    return str(value).strip().lower()


def flatten_prompt_json(prompt_json: Path, mode: str):
    """Convert class text json to detector categories and business groups."""
    raw = json.loads(prompt_json.read_text(encoding="utf-8"))
    categories: list[str] = []
    groups: list[list[int]] = []
    names: list[str] = []

    for item in raw:
        if isinstance(item, str):
            prompts = [item]
        else:
            prompts = [str(x).strip() for x in item if str(x).strip()]
        if not prompts:
            continue
        if mode == "first":
            prompts = [prompts[0]]
        elif mode != "all":
            raise ValueError(f"Unsupported prompt mode: {mode}")

        group_ids = []
        for prompt in prompts:
            group_ids.append(len(categories))
            categories.append(prompt)
        groups.append(group_ids)
        names.append(prompts[0])

    return categories, groups, names


def apply_prompt_json(detector: MambaYOLODetector, prompt_json: Path, mode: str):
    categories, groups, names = flatten_prompt_json(prompt_json, mode)
    detector.categories = categories
    detector.business_label_groups = groups
    detector.business_names = names
    detector._update_texts()
    return categories, groups, names


def label_for(class_id: int, categories: list[str]) -> str:
    if 0 <= class_id < len(categories):
        return categories[class_id]
    return f"class_{class_id}"


def draw_detections(frame: np.ndarray, detections: list[dict], categories: list[str]):
    for det in detections:
        x1, y1, x2, y2 = [int(round(x)) for x in det["box"]]
        label = label_for(int(det["class_id"]), categories)
        score = float(det["score"])
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2, cv2.LINE_AA)
        cv2.putText(
            frame,
            f"{label} {score:.2f}",
            (x1, max(22, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )


def infer_frame(detector: MambaYOLODetector, frame: np.ndarray):
    boxes, scores, idxs = detector(frame)
    boxes = np.asarray(boxes, dtype=np.float32)
    scores = np.asarray(scores, dtype=np.float32)
    idxs = np.asarray(idxs, dtype=np.int32)

    detections = []
    for box, score, class_id in zip(boxes, scores, idxs):
        detections.append(
            {
                "class_id": int(class_id),
                "score": float(score),
                "box": [float(x) for x in box.tolist()],
            }
        )
    detections.sort(key=lambda item: item["score"], reverse=True)
    return detections


def print_detections(prefix: str, detections: list[dict], categories: list[str], topk: int):
    if not detections:
        print(f"{prefix}: no detections")
        return
    shown = detections[:topk]
    rendered = []
    for det in shown:
        label = label_for(int(det["class_id"]), categories)
        rendered.append(f"{label}:{det['score']:.3f}")
    print(f"{prefix}: " + ", ".join(rendered))


def write_jsonl(records_path: Path, source: str, frame_id: int | None, detections: list[dict], categories: list[str]):
    with records_path.open("a", encoding="utf-8") as f:
        for det in detections:
            item = dict(det)
            item["source"] = source
            item["frame"] = frame_id
            item["label"] = label_for(int(det["class_id"]), categories)
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def process_image(path: Path, detector: MambaYOLODetector, output_dir: Path, records_path: Path, topk: int):
    frame = cv2.imread(str(path))
    if frame is None:
        print(f"[WARN] Cannot read image: {path}")
        return Counter()

    detections = infer_frame(detector, frame)
    categories = list(detector.categories)
    print_detections(path.name, detections, categories, topk)
    write_jsonl(records_path, str(path), None, detections, categories)

    draw_detections(frame, detections, categories)
    out_path = output_dir / f"{path.stem}_mamba.jpg"
    cv2.imwrite(str(out_path), frame)

    return Counter(label_for(int(det["class_id"]), categories) for det in detections)


def process_video(
    path: Path,
    detector: MambaYOLODetector,
    output_dir: Path,
    records_path: Path,
    topk: int,
    stride: int,
    max_frames: int,
    save_video: bool,
):
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    writer = None
    if save_video:
        out_path = output_dir / f"{path.stem}_mamba.mp4"
        writer = cv2.VideoWriter(
            str(out_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            max(fps / max(stride, 1), 1.0),
            (width, height),
        )
        print(f"[INFO] Writing annotated video: {out_path}")

    summary = Counter()
    frame_id = -1
    processed = 0
    categories = list(detector.categories)
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_id += 1
        if frame_id % max(stride, 1) != 0:
            continue
        if max_frames > 0 and processed >= max_frames:
            break

        detections = infer_frame(detector, frame)
        print_detections(f"{path.name} frame={frame_id}", detections, categories, topk)
        write_jsonl(records_path, str(path), frame_id, detections, categories)
        summary.update(label_for(int(det["class_id"]), categories) for det in detections)

        draw_detections(frame, detections, categories)
        if writer is not None:
            writer.write(frame)
        elif processed < 20:
            out_path = output_dir / f"{path.stem}_frame{frame_id:06d}.jpg"
            cv2.imwrite(str(out_path), frame)

        processed += 1

    cap.release()
    if writer is not None:
        writer.release()
    return summary


def iter_inputs(input_path: Path):
    if input_path.is_dir():
        for path in sorted(input_path.iterdir()):
            if path.suffix.lower() in IMAGE_EXTS:
                yield path
        return
    yield input_path


def parse_args():
    parser = argparse.ArgumentParser(description="Debug standalone Mamba-YOLO inference")
    parser.add_argument("--input", required=True, help="Image, image directory, or video path")
    parser.add_argument("--output-dir", default="runtime/mamba_debug", help="Directory for annotated outputs")
    parser.add_argument("--config", default=None, help="Mamba config path. Defaults to business detector config")
    parser.add_argument("--weights", default=None, help="Mamba checkpoint path. Defaults to business detector weights")
    parser.add_argument("--open-vocab", action="store_true", help="Use open-vocabulary base detector config/weights")
    parser.add_argument("--confidence", type=float, default=0.05, help="Detection threshold for debugging")
    parser.add_argument("--prompt-json", default=None, help="Optional custom_finetune_class_texts.json path")
    parser.add_argument("--prompt-mode", choices=("first", "all"), default="first", help="Use first prompt or all prompts per class from --prompt-json")
    parser.add_argument("--stride", type=int, default=1, help="Video frame stride")
    parser.add_argument("--max-frames", type=int, default=0, help="Max processed frames for video; 0 means all")
    parser.add_argument("--topk", type=int, default=20, help="Print top-k detections per frame")
    parser.add_argument("--save-video", action="store_true", help="Save annotated video for video input")
    parser.add_argument("--device", default=None, help="cuda:0 or cpu. Defaults to auto")
    return parser.parse_args()


def main():
    args = parse_args()
    output_dir = resolve_path(args.output_dir)
    assert output_dir is not None
    output_dir.mkdir(parents=True, exist_ok=True)
    records_path = output_dir / "detections.jsonl"
    if records_path.exists():
        records_path.unlink()

    if args.open_vocab:
        config_path = resolve_path(args.config or Config.MAMBA_YOLO_OPEN_CONFIG)
        weights_path = resolve_path(args.weights or Config.MAMBA_YOLO_OPEN_WEIGHTS)
    else:
        config_path = resolve_path(args.config or Config.MAMBA_YOLO_CONFIG)
        weights_path = resolve_path(args.weights or Config.MAMBA_YOLO_WEIGHTS)

    input_path = resolve_path(args.input)
    prompt_json = resolve_path(args.prompt_json)
    if input_path is None or not input_path.exists():
        raise FileNotFoundError(f"Input not found: {args.input}")
    if config_path is None or not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    if weights_path is None or not weights_path.exists():
        raise FileNotFoundError(f"Weights not found: {weights_path}")
    if prompt_json is not None and not prompt_json.exists():
        raise FileNotFoundError(f"Prompt json not found: {prompt_json}")

    print(f"[INFO] cwd={ROOT}")
    print(f"[INFO] config={config_path}")
    print(f"[INFO] weights={weights_path}")
    print(f"[INFO] confidence={args.confidence}")
    if prompt_json:
        print(f"[INFO] prompt_json={prompt_json} mode={args.prompt_mode}")

    detector = MambaYOLODetector(
        config_path=str(config_path),
        checkpoint_path=str(weights_path),
        confidence=float(args.confidence),
        extra_prompts=None,
        device=args.device,
    )

    if prompt_json:
        categories, groups, names = apply_prompt_json(detector, prompt_json, args.prompt_mode)
    else:
        categories = list(detector.categories)
        groups = list(getattr(detector, "business_label_groups", []))
        names = list(getattr(detector, "business_names", []))

    print(f"[INFO] categories({len(categories)})={categories}")
    print(f"[INFO] business_names={names}")
    print(f"[INFO] business_groups={groups}")

    total = Counter()
    for path in iter_inputs(input_path):
        ext = path.suffix.lower()
        if ext in IMAGE_EXTS:
            total.update(process_image(path, detector, output_dir, records_path, args.topk))
        elif ext in VIDEO_EXTS:
            total.update(
                process_video(
                    path,
                    detector,
                    output_dir,
                    records_path,
                    args.topk,
                    max(args.stride, 1),
                    args.max_frames,
                    args.save_video,
                )
            )
        else:
            print(f"[WARN] Unsupported input type: {path}")

    print(f"[DONE] Output dir: {output_dir}")
    print(f"[DONE] JSONL: {records_path}")
    print(f"[DONE] Summary: {dict(total)}")


if __name__ == "__main__":
    main()
