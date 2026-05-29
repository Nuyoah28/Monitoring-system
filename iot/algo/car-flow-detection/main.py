from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict
from pathlib import Path

import cv2

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from src.aggregator import FlowAggregator
from src.config import load_json
from src.counter import FlowCounter
from src.detector import LocalYoloTracker
from src.reporter import FlowReporter
from src.visualizer import draw_overlay


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run car flow detection with YOLOv13-lite + ByteTrack")
    parser.add_argument(
        "--config",
        type=str,
        default=str(CURRENT_DIR / "config" / "camera.example.json"),
        help="Path to JSON config file",
    )
    parser.add_argument("--source", type=str, default="", help="Override video source path/URL")
    parser.add_argument("--show", action="store_true", help="Display annotated frames in a window")
    parser.add_argument("--save-video", type=str, default="", help="Optional annotated output video path")
    parser.add_argument("--device", type=str, default="", help="Override device, e.g. 0 or cpu")
    parser.add_argument("--max-frames", type=int, default=0, help="Stop after N frames, 0 means no limit")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve()
    config = load_json(config_path)
    config_dir = config_path.parent

    if not config.get("model_path"):
        raise ValueError("Config field 'model_path' is required and must point to a trained .pt file.")
    config["model_path"] = _resolve_path_like(config_dir, config["model_path"])
    config["tracker_path"] = _resolve_path_like(config_dir, config["tracker_path"])
    if args.device:
        config["device"] = args.device
    if config.get("output_jsonl"):
        config["output_jsonl"] = _resolve_path_like(config_dir, config["output_jsonl"])

    source = args.source or config["source"]
    if not source:
        raise ValueError("No video source configured.")
    if _looks_like_local_path(source):
        source_base_dir = Path.cwd() if args.source else config_dir
        source = _resolve_path_like(source_base_dir, source)

    save_video = args.save_video
    if save_video and _looks_like_local_path(save_video):
        save_video = _resolve_path_like(Path.cwd(), save_video)

    print(f"[INFO] loading model: {config['model_path']}")
    tracker = LocalYoloTracker(
        model_path=config["model_path"],
        tracker_path=config["tracker_path"],
        conf=float(config.get("conf", 0.25)),
        iou=float(config.get("iou", 0.5)),
        imgsz=int(config.get("imgsz", 640)),
        device=str(config.get("device", "cpu")),
        max_det=int(config.get("max_det", 300)),
        half=bool(config.get("half", False)),
        verbose=bool(config.get("verbose", False)),
    )
    print(f"[INFO] model loaded, device={config.get('device', 'cpu')}, source={source}")

    counter = FlowCounter(camera_id=config["camera_id"], rules=config["rules"])
    aggregator = FlowAggregator()
    reporter = FlowReporter(
        output_jsonl=config.get("output_jsonl"),
        http_config=config.get("http_report", {}),
    )

    capture_source = int(source) if source.isdigit() else source
    capture = cv2.VideoCapture(capture_source)
    if not capture.isOpened():
        raise RuntimeError(f"Cannot open video source: {source}")
    print("[INFO] video opened, start processing frames...")

    if save_video:
        Path(save_video).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

    writer = None
    writer_temp_path = ""
    frame_index = 0
    last_report_monotonic = time.monotonic()

    try:
        while True:
            ok, frame = capture.read()
            if not ok or frame is None:
                break

            timestamp_ms = int(time.time() * 1000)
            tracked_objects = tracker.track(frame)
            events = counter.update(tracked_objects, frame_index=frame_index, timestamp_ms=timestamp_ms)
            for event in events:
                aggregator.add_event(event)
            occupancy = counter.occupancy_snapshot()
            snapshot = aggregator.snapshot()

            payload = {
                "cameraId": config["camera_id"],
                "timestampMs": timestamp_ms,
                "frameIndex": frame_index,
                "events": [asdict(event) for event in events],
                "occupancy": occupancy,
                "stats": snapshot,
            }

            report_interval = float(config.get("report_interval_seconds", 5))
            if events or time.monotonic() - last_report_monotonic >= report_interval:
                try:
                    reporter.emit(payload)
                except Exception as exc:  # pylint: disable=broad-except
                    print(f"[WARN] reporter emit failed: {exc}")
                last_report_monotonic = time.monotonic()

            annotated = frame.copy()
            annotated = draw_overlay(
                annotated,
                rules=config["rules"],
                tracked_objects=tracked_objects,
                track_history=counter.track_history,
                snapshot=snapshot,
                occupancy=occupancy,
                events=events,
            )

            if save_video:
                if writer is None:
                    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                    height, width = annotated.shape[:2]
                    fps = capture.get(cv2.CAP_PROP_FPS) or 15.0
                    writer, writer_temp_path = _create_video_writer(save_video, fourcc, fps, (width, height))
                writer.write(annotated)

            if args.show:
                cv2.imshow("Car Flow Detection", annotated)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            frame_index += 1
            if frame_index == 1 or frame_index % 30 == 0:
                print(f"[INFO] processed {frame_index} frames")
            if args.max_frames > 0 and frame_index >= args.max_frames:
                break
    finally:
        capture.release()
        if writer is not None:
            writer.release()
            _finalize_video_output(save_video, writer_temp_path)
        if args.show:
            cv2.destroyAllWindows()


def _resolve_path_like(base_dir: Path, value: str) -> str:
    path = Path(value).expanduser()
    if path.is_absolute():
        return str(path.resolve())
    return str((base_dir / path).resolve())


def _looks_like_local_path(value: str) -> bool:
    lowered = value.lower()
    return "://" not in lowered and not lowered.isdigit()


def _create_video_writer(save_video: str, fourcc: int, fps: float, size: tuple[int, int]):
    writer = cv2.VideoWriter(save_video, fourcc, fps, size)
    if writer.isOpened():
        return writer, ""

    temp_dir = Path(tempfile.gettempdir()) / "monitoring_system_video"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / Path(save_video).name
    writer = cv2.VideoWriter(str(temp_path), fourcc, fps, size)
    if not writer.isOpened():
        raise RuntimeError(f"Cannot open video writer for target or temp path: {save_video}")
    print(f"[WARN] target video path not writable by OpenCV, using temp path: {temp_path}")
    return writer, str(temp_path)


def _finalize_video_output(save_video: str, temp_path: str) -> None:
    if not temp_path:
        return
    temp_file = Path(temp_path)
    target_file = Path(save_video)
    if not temp_file.exists():
        raise FileNotFoundError(f"Temporary video file not found: {temp_file}")
    target_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.move(str(temp_file), str(target_file))
    except PermissionError:
        command = [
            "powershell",
            "-NoProfile",
            "-Command",
            f"Copy-Item -LiteralPath '{temp_file}' -Destination '{target_file}' -Force",
        ]
        subprocess.run(command, check=True)
        temp_file.unlink(missing_ok=True)
    print(f"[INFO] moved temp video to: {target_file}")


if __name__ == "__main__":
    main()


'''
python main.py `
  --config ./config/camera.example.json `
  --source "../../test_video/raw/carflow.mp4" `
  --save-video "../../test_video/processed/carflow_processed.mp4" 
'''
