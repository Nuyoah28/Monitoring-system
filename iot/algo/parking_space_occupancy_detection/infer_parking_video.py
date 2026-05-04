from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import cv2
import numpy as np
import torch
from torch import nn
from torchvision import transforms
from torchvision.models import mobilenet_v3_small


ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run parking occupancy classification on a video.")
    parser.add_argument("--source", default="../img/parking/parking_crop.mp4", help="Video path or camera index")
    parser.add_argument("--mask", default="../img/parking/mask_crop.png", help="Parking-space mask image")
    parser.add_argument("--model", default="../img/parking/model/mobilenetv3_parking.pt", help="MobileNetV3 checkpoint path")
    parser.add_argument("--device", default="0", help="Device, e.g. 0 or cpu")
    parser.add_argument("--output-dir", default="runs/parking_classifier", help="Directory for default outputs")
    parser.add_argument("--output-video", default="", help="Annotated output video path")
    parser.add_argument("--jsonl", default="", help="Per-frame parking status JSONL path")
    parser.add_argument("--max-frames", type=int, default=0, help="Stop after N frames, 0 means all")
    parser.add_argument("--vid-stride", type=int, default=1, help="Process every Nth frame")
    parser.add_argument("--min-space-area", type=int, default=100, help="Ignore mask components smaller than this")
    parser.add_argument("--show", action="store_true", help="Show live preview window")
    parser.add_argument("--no-save-video", action="store_true", help="Do not write annotated video")
    return parser.parse_args()


def resolve_path(base: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return (base / path).resolve()


def read_image(path: Path):
    data = np.fromfile(str(path), dtype=np.uint8)
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def create_model(num_classes: int) -> nn.Module:
    model = mobilenet_v3_small(weights=None)
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Linear(in_features, num_classes)
    return model


def resolve_device(raw: str) -> torch.device:
    if raw == "cpu" or not torch.cuda.is_available():
        return torch.device("cpu")
    return torch.device(f"cuda:{raw}")


def load_model(path: Path, device: torch.device):
    checkpoint = torch.load(path, map_location=device, weights_only=True)
    class_names = checkpoint.get("class_names", ["empty", "not_empty"])
    image_size = int(checkpoint.get("image_size", 96))
    model = create_model(num_classes=len(class_names))
    model.load_state_dict(checkpoint["model_state"])
    model.to(device)
    model.eval()
    preprocess = transforms.Compose(
        [
            transforms.ToPILImage(),
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
    return model, preprocess, class_names


def extract_spaces(mask, frame_shape, min_area: int) -> list[dict]:
    frame_height, frame_width = frame_shape[:2]
    if mask.shape[:2] != (frame_height, frame_width):
        mask = cv2.resize(mask, (frame_width, frame_height), interpolation=cv2.INTER_NEAREST)

    gray = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
    binary = (gray > 0).astype(np.uint8)
    total_labels, _, stats, _ = cv2.connectedComponentsWithStats(binary, 8)

    spaces = []
    for label_id in range(1, total_labels):
        x = int(stats[label_id, cv2.CC_STAT_LEFT])
        y = int(stats[label_id, cv2.CC_STAT_TOP])
        w = int(stats[label_id, cv2.CC_STAT_WIDTH])
        h = int(stats[label_id, cv2.CC_STAT_HEIGHT])
        area = int(stats[label_id, cv2.CC_STAT_AREA])
        if area < min_area:
            continue
        spaces.append({"id": str(len(spaces) + 1), "bbox": [x, y, w, h], "area": area})

    spaces.sort(key=lambda item: (item["bbox"][1], item["bbox"][0]))
    for index, space in enumerate(spaces, start=1):
        space["id"] = str(index)
    return spaces


def classify_space(model, preprocess, class_names: list[str], device: torch.device, crop) -> tuple[str, int, float]:
    if crop.size == 0:
        return "unknown", -1, 0.0
    crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
    image_tensor = preprocess(crop_rgb).unsqueeze(0).to(device)
    with torch.inference_mode():
        probs = torch.softmax(model(image_tensor), dim=1)[0]
    label = int(torch.argmax(probs).item())
    confidence = float(probs[label].item())
    class_name = class_names[label]
    return ("free" if class_name == "empty" else "occupied"), label, confidence


def classify_frame(model, preprocess, class_names: list[str], device: torch.device, frame, spaces: list[dict]) -> tuple[dict, list[dict]]:
    states = []
    occupied = 0
    free = 0
    unknown = 0
    height, width = frame.shape[:2]

    for space in spaces:
        x, y, w, h = space["bbox"]
        x1 = max(0, min(width, x))
        y1 = max(0, min(height, y))
        x2 = max(0, min(width, x + w))
        y2 = max(0, min(height, y + h))
        crop = frame[y1:y2, x1:x2]
        status, raw_label, confidence = classify_space(model, preprocess, class_names, device, crop)
        if status == "occupied":
            occupied += 1
        elif status == "free":
            free += 1
        else:
            unknown += 1
        states.append(
            {
                "id": space["id"],
                "status": status,
                "label": raw_label,
                "confidence": confidence,
                "bbox": [x1, y1, x2 - x1, y2 - y1],
            }
        )

    total = len(spaces)
    stats = {
        "total_spaces": total,
        "occupied": occupied,
        "free": free,
        "unknown": unknown,
        "occupancy_rate": None if total == 0 else occupied / total,
    }
    return stats, states


def draw_overlay(frame, stats: dict, states: list[dict]) -> None:
    for state in states:
        x, y, w, h = state["bbox"]
        occupied = state["status"] == "occupied"
        color = (0, 0, 255) if occupied else (0, 180, 0)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        label = f"{state['id']}:{'occ' if occupied else state['status']}"
        cv2.putText(frame, label, (x, max(18, y - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

    rate = stats["occupancy_rate"]
    summary = (
        f"occupied={stats['occupied']} free={stats['free']} unknown={stats['unknown']}"
        if rate is None
        else f"occupied={stats['occupied']} free={stats['free']} rate={rate * 100:.1f}%"
    )
    cv2.rectangle(frame, (8, 8), (520, 46), (0, 0, 0), -1)
    cv2.putText(frame, summary, (18, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)


def main() -> None:
    args = parse_args()
    source = args.source
    capture_source = int(source) if source.isdigit() else str(resolve_path(ROOT, source))
    mask_path = resolve_path(ROOT, args.mask)
    model_path = resolve_path(ROOT, args.model)
    device = resolve_device(args.device)
    output_dir = resolve_path(ROOT, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_stem = f"camera_{source}" if isinstance(capture_source, int) else Path(capture_source).stem
    stamp = time.strftime("%Y%m%d_%H%M%S")
    output_video = Path(args.output_video) if args.output_video else output_dir / f"{source_stem}_{stamp}.mp4"
    jsonl_path = Path(args.jsonl) if args.jsonl else output_dir / f"{source_stem}_{stamp}.jsonl"
    if not output_video.is_absolute():
        output_video = (ROOT / output_video).resolve()
    if not jsonl_path.is_absolute():
        jsonl_path = (ROOT / jsonl_path).resolve()
    output_video.parent.mkdir(parents=True, exist_ok=True)
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    model, preprocess, class_names = load_model(model_path, device)
    mask = read_image(mask_path)
    if mask is None:
        raise FileNotFoundError(f"Cannot read mask image: {mask_path}")

    capture = cv2.VideoCapture(capture_source)
    if not capture.isOpened():
        raise RuntimeError(f"Cannot open video source: {args.source}")

    ok, first_frame = capture.read()
    if not ok or first_frame is None:
        raise RuntimeError(f"Cannot read first frame from source: {args.source}")
    spaces = extract_spaces(mask, first_frame.shape, args.min_space_area)
    if not spaces:
        raise ValueError(f"No parking spaces found from mask: {mask_path}")
    print(f"[INFO] loaded MobileNetV3 classifier: {model_path}")
    print(f"[INFO] classes: {class_names}, device={device}")
    print(f"[INFO] extracted parking spaces: {len(spaces)}")

    fps = capture.get(cv2.CAP_PROP_FPS) or 25.0
    height, width = first_frame.shape[:2]
    writer = None
    if not args.no_save_video:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(output_video), fourcc, fps, (width, height))

    frame_index = 0
    processed = 0
    try:
        with jsonl_path.open("w", encoding="utf-8") as jsonl_file:
            frame = first_frame
            while True:
                if args.vid_stride <= 1 or frame_index % args.vid_stride == 0:
                    stats, states = classify_frame(model, preprocess, class_names, device, frame, spaces)
                    payload = {
                        "frame_index": frame_index,
                        "timestamp_ms": int(time.time() * 1000),
                        **stats,
                        "spaces": states,
                    }
                    jsonl_file.write(json.dumps(payload, ensure_ascii=False) + "\n")

                    annotated = frame.copy()
                    draw_overlay(annotated, stats, states)
                    if writer is not None:
                        writer.write(annotated)
                    if args.show:
                        cv2.imshow("Parking Occupancy Classification", annotated)
                        if cv2.waitKey(1) & 0xFF == ord("q"):
                            break

                    processed += 1
                    if args.max_frames > 0 and processed >= args.max_frames:
                        break

                ok, frame = capture.read()
                if not ok or frame is None:
                    break
                frame_index += 1
    finally:
        capture.release()
        if writer is not None:
            writer.release()
        if args.show:
            cv2.destroyAllWindows()

    print(f"Processed frames: {processed}")
    print(f"Stats JSONL: {jsonl_path}")
    if not args.no_save_video:
        print(f"Annotated video: {output_video}")


if __name__ == "__main__":
    main()


'''
python ./infer_parking_video.py `
  --source ../img/parking/parking_crop.mp4 `
  --mask ../img/parking/mask_crop.png `
  --model ../img/parking/model/mobilenetv3_parking.pt `
  --device 0 `
  --output-video ../test_video/processed/parking_classifier_processed.mp4 `
  --jsonl ../test_video/processed/parking_classifier_stats.jsonl
'''
