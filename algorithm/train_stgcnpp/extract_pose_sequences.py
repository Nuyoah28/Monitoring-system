import argparse
import os
from pathlib import Path

import cv2
import numpy as np

from Yolov8.Yolov8_Pose import LoadPoseEngine


VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".flv", ".MP4", ".AVI", ".MOV", ".MKV", ".FLV"}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract per-person pose sequences from class-folder videos."
    )
    parser.add_argument(
        "--input-root",
        required=True,
        help="Input root with class subfolders, e.g. normal/fall/punch/wave/*.mp4",
    )
    parser.add_argument(
        "--output-root",
        required=True,
        help="Output root for .npy pose sequences.",
    )
    parser.add_argument(
        "--pose-engine",
        default="algo/yolov8n-pose.engine",
        help="Path to yolov8 pose TensorRT engine.",
    )
    parser.add_argument("--min-frames", type=int, default=20, help="Minimum frames to keep one sequence.")
    parser.add_argument("--max-frames", type=int, default=120, help="Maximum frames per saved sequence.")
    parser.add_argument("--frame-step", type=int, default=1, help="Use every Nth frame.")
    parser.add_argument("--iou-thres", type=float, default=0.3, help="IoU threshold for track association.")
    parser.add_argument("--max-missing", type=int, default=8, help="Track expires after missing this many frames.")
    return parser.parse_args()


def iou(a, b):
    xa1, ya1, xa2, ya2 = a
    xb1, yb1, xb2, yb2 = b
    ix1 = max(xa1, xb1)
    iy1 = max(ya1, yb1)
    ix2 = min(xa2, xb2)
    iy2 = min(ya2, yb2)
    iw = max(0.0, ix2 - ix1)
    ih = max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    aa = max(0.0, xa2 - xa1) * max(0.0, ya2 - ya1)
    ab = max(0.0, xb2 - xb1) * max(0.0, yb2 - yb1)
    den = aa + ab - inter
    return inter / den if den > 1e-6 else 0.0


def save_track_segments(seq_list, out_dir, base_name, min_frames, max_frames):
    saved = 0
    if len(seq_list) < min_frames:
        return 0
    out_dir.mkdir(parents=True, exist_ok=True)
    arr = np.asarray(seq_list, dtype=np.float32)  # (T,17,3)
    start = 0
    seg_idx = 0
    while start < arr.shape[0]:
        end = min(start + max_frames, arr.shape[0])
        seg = arr[start:end]
        if seg.shape[0] >= min_frames:
            out_path = out_dir / f"{base_name}_seg{seg_idx:03d}.npy"
            np.save(out_path, seg)
            saved += 1
            seg_idx += 1
        start = end
    return saved


def iter_videos(class_dir):
    for p in sorted(class_dir.rglob("*")):
        if p.is_file() and p.suffix in VIDEO_EXTS:
            yield p


def process_video(video_path, class_out_dir, infer, min_frames, max_frames, frame_step, iou_thres, max_missing):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"[WARN] cannot open video: {video_path}")
        return 0

    track_boxes = {}     # tid -> box
    track_seq = {}       # tid -> [np.array(17,3), ...]
    track_missing = {}   # tid -> int
    next_tid = 1
    frame_idx = 0
    saved_total = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx += 1
        if frame_step > 1 and frame_idx % frame_step != 0:
            continue

        try:
            bboxes, _, points = infer(frame)
            bboxes = bboxes.to(np.int32).cpu().numpy()
            points = points.cpu().numpy()
        except Exception as e:
            print(f"[WARN] infer failed in {video_path.name}: {e}")
            continue

        det_n = len(bboxes)
        assigned = [-1] * det_n
        tids = list(track_boxes.keys())

        pairs = []
        for di in range(det_n):
            db = bboxes[di].astype(np.float32)
            for tid in tids:
                score = iou(db, track_boxes[tid])
                if score >= iou_thres:
                    pairs.append((score, di, tid))
        pairs.sort(reverse=True, key=lambda x: x[0])

        used_d = set()
        used_t = set()
        for _, di, tid in pairs:
            if di in used_d or tid in used_t:
                continue
            assigned[di] = tid
            used_d.add(di)
            used_t.add(tid)

        # increase missing count first
        for tid in list(track_missing.keys()):
            track_missing[tid] += 1

        # update tracks
        for di in range(det_n):
            tid = assigned[di]
            if tid == -1:
                tid = next_tid
                next_tid += 1
                track_seq[tid] = []
                track_missing[tid] = 0
            track_boxes[tid] = bboxes[di].astype(np.float32)
            track_missing[tid] = 0
            kp = points[di].reshape(17, 3).astype(np.float32)
            track_seq[tid].append(kp)

        # flush expired tracks
        expired = [tid for tid, miss in track_missing.items() if miss > max_missing]
        for tid in expired:
            base_name = f"{video_path.stem}_track{tid:03d}"
            saved_total += save_track_segments(
                track_seq.get(tid, []),
                class_out_dir,
                base_name,
                min_frames=min_frames,
                max_frames=max_frames,
            )
            track_boxes.pop(tid, None)
            track_seq.pop(tid, None)
            track_missing.pop(tid, None)

    cap.release()

    # flush remaining tracks
    for tid, seq in list(track_seq.items()):
        base_name = f"{video_path.stem}_track{tid:03d}"
        saved_total += save_track_segments(
            seq,
            class_out_dir,
            base_name,
            min_frames=min_frames,
            max_frames=max_frames,
        )
    return saved_total


def main():
    args = parse_args()
    input_root = Path(args.input_root).resolve()
    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    if not input_root.exists():
        raise FileNotFoundError(f"input root not found: {input_root}")
    if args.frame_step < 1:
        raise ValueError("--frame-step must be >= 1")

    infer = LoadPoseEngine(args.pose_engine)
    total_saved = 0
    total_videos = 0

    for class_dir in sorted(input_root.iterdir()):
        if not class_dir.is_dir():
            continue
        class_name = class_dir.name.strip().lower()
        class_out_dir = output_root / class_name
        class_count = 0

        videos = list(iter_videos(class_dir))
        if not videos:
            continue
        print(f"[INFO] class={class_name}, videos={len(videos)}")

        for vp in videos:
            total_videos += 1
            saved = process_video(
                video_path=vp,
                class_out_dir=class_out_dir,
                infer=infer,
                min_frames=args.min_frames,
                max_frames=args.max_frames,
                frame_step=args.frame_step,
                iou_thres=args.iou_thres,
                max_missing=args.max_missing,
            )
            class_count += saved
            print(f"  - {vp.name}: saved {saved} sequences")

        total_saved += class_count
        print(f"[INFO] class={class_name}, total saved={class_count}")

    print(f"[DONE] videos={total_videos}, sequences={total_saved}, output={output_root}")


if __name__ == "__main__":
    main()
