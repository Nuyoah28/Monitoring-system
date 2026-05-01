import argparse
import json
import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import torch

from fix_imports import apply_patches

apply_patches()

from mmdet.apis import init_detector, inference_detector
from mmdet.utils import register_all_modules
from Yolov8.utils1 import draw_on_src
from Yolov8.utils1 import update_event_names
from common import monitor as monitorCommon


CASE_NAMES = [
    "danger_zone",
    "smoke",
    "area_loitering",
    "fall",
    "fire",
    "smoking",
    "punch",
    "garbage",
    "ice",
    "ebike",
    "vehicle",
    "wave",
]


def _find_videos(input_dir: Path, recursive: bool) -> list[Path]:
    patterns = ("*.mp4", "*.MP4")
    videos = []
    if recursive:
        for pattern in patterns:
            videos.extend(input_dir.rglob(pattern))
    else:
        for pattern in patterns:
            videos.extend(input_dir.glob(pattern))
    return sorted(videos)


def _build_type_list(enable_all: bool) -> list[bool]:
    def disable_pose_related(src: list[bool]) -> list[bool]:
        result = list(src)
        for idx in (0, 2, 3, 5, 6, 11):
            result[idx] = False
        return result

    if not enable_all:
        return disable_pose_related(list(monitorCommon.TYPE_LIST))

    result = [False] * 12
    for idx in (1, 4, 7, 9, 10):
        result[idx] = True
    return result


def _load_class_names_from_json(class_text_json: Path) -> list[str]:
    with open(class_text_json, "r", encoding="utf-8") as f:
        class_texts = json.load(f)

    class_names = []
    for item in class_texts:
        if isinstance(item, list) and item:
            class_names.append(str(item[0]).strip())
        elif isinstance(item, str):
            class_names.append(item.strip())
    return class_names


def _load_models(root: Path, confidence: float, class_text_json: Path):
    mamba_root = root / "Mamba-YOLO-World"
    mamba_cfg = root / "Mamba-YOLO-World" / "configs" / "mamba2_yolo_world_s_finetune_custom.py"
    mamba_ckpt = root / "algo" / "best_coco_overflow_precision_epoch_90.pth"

    mamba_root_str = str(mamba_root.resolve())
    if mamba_root_str not in sys.path:
        sys.path.insert(0, mamba_root_str)

    class_names = _load_class_names_from_json(class_text_json)
    register_all_modules()
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    model = init_detector(str(mamba_cfg), str(mamba_ckpt), device=device, palette="random")

    class_text_json_abs = str(class_text_json.resolve())

    # Align finetune config paths for inference-only environment.
    # Some configs use relative paths like data/texts/*.json which may not exist
    # under current working directory.
    def _patch_text_path_in_pipeline(pipeline_cfg):
        for t in pipeline_cfg:
            if isinstance(t, dict) and t.get("type") == "LoadText":
                t["text_path"] = class_text_json_abs

    dataset_cfg = model.cfg.test_dataloader.dataset
    if hasattr(dataset_cfg, "pipeline"):
        _patch_text_path_in_pipeline(dataset_cfg.pipeline)
    if hasattr(dataset_cfg, "class_text_path"):
        dataset_cfg.class_text_path = class_text_json_abs

    update_event_names(class_names)
    return model, class_names


def _process_one_video(
    video_path: Path,
    out_dir: Path,
    model,
    class_names: list[str],
    type_list: list[bool],
    save_video: bool,
    frame_step: int,
    confidence: float,
):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return {
            "video": str(video_path),
            "status": "failed",
            "reason": "cannot_open_video",
        }

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 25.0

    writer = None
    out_video_path = out_dir / f"{video_path.stem}_pred.mp4"
    if save_video:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(out_video_path), fourcc, fps, (640, 480))

    frame_count = 0
    processed_count = 0
    warning_hit_counts = [0] * 12
    start = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            if frame_step > 1 and frame_count % frame_step != 0:
                continue

            processed_count += 1
            pred_frame = frame
            warning_list = [False] * 12

            result = inference_detector(model, pred_frame)
            pred_instances = result.pred_instances
            pred_instances = pred_instances[pred_instances.scores.float() > confidence]
            pred_instances = pred_instances.cpu().numpy()

            if len(pred_instances["bboxes"]) > 0:
                boxes1 = pred_instances["bboxes"].astype(np.float32)
                idxs1 = pred_instances["labels"].astype(np.int32)
                draw_on_src(pred_frame, boxes1, idxs1)

                name_to_id = {name.lower(): i for i, name in enumerate(class_names)}
                fire_id = name_to_id.get("fire", -1)
                smoke_id = name_to_id.get("smoke", -1)
                garbage_ids = [
                    i for n, i in name_to_id.items()
                    if n in ("garbage", "overflow")
                ]
                ebike_ids = [
                    i for n, i in name_to_id.items()
                    if n in ("bicycle", "motorcycle")
                ]

                if type_list[4] and fire_id >= 0 and np.any(idxs1 == fire_id):
                    warning_list[4] = True
                if type_list[1] and smoke_id >= 0 and np.any(idxs1 == smoke_id):
                    warning_list[1] = True
                if type_list[7] and len(garbage_ids) > 0 and np.any(np.isin(idxs1, garbage_ids)):
                    warning_list[7] = True
                if type_list[9] and len(ebike_ids) > 0 and np.any(np.isin(idxs1, ebike_ids)):
                    warning_list[9] = True

            pred_frame = cv2.resize(pred_frame, (640, 480))

            for idx, flag in enumerate(warning_list):
                if flag:
                    warning_hit_counts[idx] += 1

            if writer is not None:
                writer.write(pred_frame)

            if processed_count % 100 == 0:
                print(f"[{video_path.name}] processed frames: {processed_count}")
    finally:
        cap.release()
        if writer is not None:
            writer.release()

    elapsed = time.time() - start
    return {
        "video": str(video_path),
        "status": "ok",
        "total_frames": frame_count,
        "processed_frames": processed_count,
        "elapsed_sec": round(elapsed, 3),
        "output_video": str(out_video_path) if save_video else None,
        "warning_hits": {CASE_NAMES[i]: warning_hit_counts[i] for i in range(12)},
    }


def main():
    parser = argparse.ArgumentParser(description="Read all mp4 files in a folder and run prediction.")
    parser.add_argument("--input-dir", default="./test_video/raw", help="Folder containing mp4 files")
    parser.add_argument("--output-dir", default="./test_video/processed", help="Output folder for videos and report")
    parser.add_argument("--recursive", action="store_true", help="Search mp4 recursively")
    parser.add_argument("--no-save-video", action="store_true", help="Do not save rendered prediction video")
    parser.add_argument("--frame-step", type=int, default=1, help="Process every N-th frame")
    parser.add_argument("--confidence", type=float, default=0.4, help="Mamba-YOLO confidence threshold")
    parser.add_argument("--enable-all", action="store_true", help="Enable all implemented event types")
    parser.add_argument(
        "--class-text-json",
        default="./Mamba-YOLO-World/data/custom_finetune_class_texts.json",
        help="Class text json used by finetune config",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    input_dir = Path(args.input_dir).resolve()
    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists() or not input_dir.is_dir():
        raise ValueError(f"invalid input dir: {input_dir}")

    videos = _find_videos(input_dir, recursive=args.recursive)
    if not videos:
        print(f"No mp4 files found under: {input_dir}")
        return

    if args.frame_step < 1:
        raise ValueError("--frame-step must be >= 1")

    class_text_json = Path(args.class_text_json).resolve()
    if not class_text_json.exists():
        raise ValueError(f"class text json not found: {class_text_json}")

    type_list = _build_type_list(enable_all=args.enable_all)
    print("Loading models...")
    model, class_names = _load_models(root, confidence=args.confidence, class_text_json=class_text_json)
    print("Models loaded.")

    all_results = []
    for idx, video_path in enumerate(videos, start=1):
        print(f"[{idx}/{len(videos)}] Processing: {video_path}")
        result = _process_one_video(
            video_path=video_path,
            out_dir=out_dir,
            model=model,
            class_names=class_names,
            type_list=type_list,
            save_video=not args.no_save_video,
            frame_step=args.frame_step,
            confidence=args.confidence,
        )
        all_results.append(result)
        print(f"Done: {video_path.name} -> {result['status']}")

    report = {
        "input_dir": str(input_dir),
        "output_dir": str(out_dir),
        "video_count": len(videos),
        "results": all_results,
    }
    report_path = out_dir / "prediction_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"All done. Report saved to: {report_path}")


if __name__ == "__main__":
    main()
