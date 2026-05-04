from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DEFAULT_MODELS_DIR = PROJECT_DIR / "models"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test exported ONNX and MNN vehicle-flow models.")
    parser.add_argument("--models-dir", default=str(DEFAULT_MODELS_DIR), help="Directory containing onnx/ and mnn/.")
    parser.add_argument("--image", help="Input image path. If omitted, use first image from --data val split.")
    parser.add_argument("--data", default=str(PROJECT_DIR / "datasets" / "vehicle_flow.yaml"), help="Dataset yaml.")
    parser.add_argument("--weights", nargs="*", help="Model stems or paths. Defaults to all ONNX/MNN models.")
    parser.add_argument("--imgsz", type=int, default=960, help="Inference image size.")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold.")
    parser.add_argument("--iou", type=float, default=0.45, help="NMS IoU threshold.")
    parser.add_argument("--warmup", type=int, default=3, help="Warmup runs per backend/model.")
    parser.add_argument("--runs", type=int, default=10, help="Timed runs per backend/model.")
    parser.add_argument("--providers", nargs="*", help="ONNX Runtime providers. Default auto-selects CUDA if present.")
    parser.add_argument("--mnn-backend", default="CPU", choices=["CPU", "OPENCL", "VULKAN"], help="MNN backend.")
    parser.add_argument("--mnn-threads", type=int, default=4, help="MNN CPU thread count.")
    parser.add_argument("--save-dir", default=str(PROJECT_DIR / "outputs" / "export_test"), help="Output directory.")
    parser.add_argument("--no-draw", action="store_true", help="Do not save visualized detection images.")
    return parser.parse_args()


def resolve_path(value: str | Path, base: Path = PROJECT_DIR) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def resolve_data_yaml(value: str | Path) -> Path:
    requested = resolve_path(value, Path.cwd())
    candidates = [
        requested,
        PROJECT_DIR / "datasets" / "vehicle_flow.yaml",
        PROJECT_DIR / "datasets" / "vehicle_flow" / "vehicle_flow.yaml",
        PROJECT_DIR / "datasets" / "vehicle_flow_single" / "vehicle_flow.yaml",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    joined = "\n".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(f"Cannot find dataset yaml. Checked:\n{joined}")


def collect_dataset_image(data_yaml: Path) -> Path:
    import yaml

    with data_yaml.open("r", encoding="utf-8") as file:
        payload = yaml.safe_load(file)

    dataset_root = data_yaml.parent
    if payload.get("path"):
        path_value = Path(payload["path"])
        dataset_root = path_value if path_value.is_absolute() else (data_yaml.parent / path_value).resolve()

    split_value = payload.get("val") or payload.get("test") or payload.get("train")
    if split_value is None:
        raise FileNotFoundError(f"No train/val/test split found in dataset yaml: {data_yaml}")

    candidates = split_value if isinstance(split_value, list) else [split_value]
    for candidate in candidates:
        candidate_path = Path(candidate)
        if not candidate_path.is_absolute():
            candidate_path = (dataset_root / candidate_path).resolve()
        if candidate_path.is_dir():
            images = sorted(path for path in candidate_path.rglob("*") if path.suffix.lower() in IMAGE_SUFFIXES)
            if images:
                return images[0]
        if candidate_path.is_file() and candidate_path.suffix.lower() in IMAGE_SUFFIXES:
            return candidate_path
        if candidate_path.is_file() and candidate_path.suffix.lower() == ".txt":
            for raw in candidate_path.read_text(encoding="utf-8").splitlines():
                raw = raw.strip()
                if not raw:
                    continue
                image_path = Path(raw)
                if not image_path.is_absolute():
                    image_path = (dataset_root / image_path).resolve()
                if image_path.exists():
                    return image_path

    raise FileNotFoundError(f"No image found from dataset yaml: {data_yaml}")


def letterbox(image: Image.Image, imgsz: int) -> tuple[np.ndarray, tuple[float, tuple[float, float]]]:
    width, height = image.size
    scale = min(imgsz / width, imgsz / height)
    new_width, new_height = int(round(width * scale)), int(round(height * scale))
    resized = image.resize((new_width, new_height), Image.BILINEAR)
    canvas = Image.new("RGB", (imgsz, imgsz), (114, 114, 114))
    pad_x = (imgsz - new_width) / 2
    pad_y = (imgsz - new_height) / 2
    canvas.paste(resized, (int(round(pad_x - 0.1)), int(round(pad_y - 0.1))))

    array = np.asarray(canvas, dtype=np.float32) / 255.0
    array = np.transpose(array, (2, 0, 1))[None]
    return np.ascontiguousarray(array), (scale, (pad_x, pad_y))


def xywh_to_xyxy(boxes: np.ndarray) -> np.ndarray:
    xyxy = boxes.copy()
    xyxy[:, 0] = boxes[:, 0] - boxes[:, 2] / 2
    xyxy[:, 1] = boxes[:, 1] - boxes[:, 3] / 2
    xyxy[:, 2] = boxes[:, 0] + boxes[:, 2] / 2
    xyxy[:, 3] = boxes[:, 1] + boxes[:, 3] / 2
    return xyxy


def box_iou_one_to_many(box: np.ndarray, boxes: np.ndarray) -> np.ndarray:
    inter_x1 = np.maximum(box[0], boxes[:, 0])
    inter_y1 = np.maximum(box[1], boxes[:, 1])
    inter_x2 = np.minimum(box[2], boxes[:, 2])
    inter_y2 = np.minimum(box[3], boxes[:, 3])
    inter_w = np.maximum(0.0, inter_x2 - inter_x1)
    inter_h = np.maximum(0.0, inter_y2 - inter_y1)
    inter = inter_w * inter_h
    area_a = max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])
    area_b = np.maximum(0.0, boxes[:, 2] - boxes[:, 0]) * np.maximum(0.0, boxes[:, 3] - boxes[:, 1])
    return inter / np.maximum(area_a + area_b - inter, 1e-7)


def nms(boxes: np.ndarray, scores: np.ndarray, iou_thr: float) -> list[int]:
    order = scores.argsort()[::-1]
    keep: list[int] = []
    while order.size:
        index = int(order[0])
        keep.append(index)
        if order.size == 1:
            break
        ious = box_iou_one_to_many(boxes[index], boxes[order[1:]])
        order = order[1:][ious <= iou_thr]
    return keep


def parse_yolo_output(
    outputs: list[np.ndarray],
    conf_thr: float,
    iou_thr: float,
    ratio_pad: tuple[float, tuple[float, float]],
    original_size: tuple[int, int],
) -> np.ndarray:
    output = max(outputs, key=lambda item: item.size)
    output = np.asarray(output)
    if output.ndim == 3:
        output = output[0]
    if output.ndim != 2:
        return np.empty((0, 6), dtype=np.float32)

    if output.shape[0] in {5, 6} or output.shape[0] < output.shape[1]:
        output = output.T

    if output.shape[1] < 5:
        return np.empty((0, 6), dtype=np.float32)

    boxes_xywh = output[:, :4].astype(np.float32)
    if output.shape[1] == 5:
        scores = output[:, 4].astype(np.float32)
        classes = np.zeros_like(scores, dtype=np.float32)
    else:
        class_scores = output[:, 4:].astype(np.float32)
        classes = class_scores.argmax(axis=1).astype(np.float32)
        scores = class_scores.max(axis=1)

    mask = scores >= conf_thr
    if not np.any(mask):
        return np.empty((0, 6), dtype=np.float32)

    boxes = xywh_to_xyxy(boxes_xywh[mask])
    scores = scores[mask]
    classes = classes[mask]
    keep = nms(boxes, scores, iou_thr)
    boxes = boxes[keep]
    scores = scores[keep]
    classes = classes[keep]

    scale, (pad_x, pad_y) = ratio_pad
    boxes[:, [0, 2]] = (boxes[:, [0, 2]] - pad_x) / scale
    boxes[:, [1, 3]] = (boxes[:, [1, 3]] - pad_y) / scale
    width, height = original_size
    boxes[:, [0, 2]] = boxes[:, [0, 2]].clip(0, width)
    boxes[:, [1, 3]] = boxes[:, [1, 3]].clip(0, height)
    return np.concatenate([boxes, scores[:, None], classes[:, None]], axis=1)


def draw_detections(image: Image.Image, detections: np.ndarray, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas = image.copy()
    draw = ImageDraw.Draw(canvas)
    for x1, y1, x2, y2, score, _cls in detections:
        draw.rectangle((float(x1), float(y1), float(x2), float(y2)), outline=(255, 40, 40), width=2)
        draw.text((float(x1), max(0.0, float(y1) - 12)), f"vehicle {score:.2f}", fill=(255, 40, 40))
    canvas.save(output_path)


def collect_models(models_dir: Path, weights: list[str] | None) -> dict[str, dict[str, Path]]:
    result: dict[str, dict[str, Path]] = {}
    for subdir, suffix in [("onnx", ".onnx"), ("mnn", ".mnn")]:
        model_dir = models_dir / subdir
        if not model_dir.exists():
            continue
        paths = [resolve_path(item, model_dir) for item in weights] if weights else sorted(model_dir.glob(f"*{suffix}"))
        for path in paths:
            if path.suffix.lower() != suffix:
                path = model_dir / f"{path.stem}{suffix}"
            if path.exists():
                result.setdefault(path.stem, {})[subdir] = path
    return result


def run_onnx(model_path: Path, input_array: np.ndarray, providers: list[str] | None, warmup: int, runs: int) -> tuple[list[np.ndarray], float]:
    import onnxruntime as ort

    available = ort.get_available_providers()
    if providers:
        active_providers = providers
    elif "CUDAExecutionProvider" in available:
        active_providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    else:
        active_providers = ["CPUExecutionProvider"]

    session = ort.InferenceSession(str(model_path), providers=active_providers)
    input_name = session.get_inputs()[0].name
    for _ in range(warmup):
        session.run(None, {input_name: input_array})

    start = time.perf_counter()
    outputs = None
    for _ in range(runs):
        outputs = session.run(None, {input_name: input_array})
    elapsed_ms = (time.perf_counter() - start) * 1000.0 / max(runs, 1)
    return [np.asarray(item) for item in outputs or []], elapsed_ms


def run_mnn(
    model_path: Path,
    input_array: np.ndarray,
    backend: str,
    threads: int,
    warmup: int,
    runs: int,
) -> tuple[list[np.ndarray], float]:
    import MNN

    interpreter = MNN.Interpreter(str(model_path))
    session = interpreter.createSession({"backend": backend, "numThread": threads})
    input_tensor = interpreter.getSessionInput(session)
    input_shape = list(input_tensor.getShape())
    if input_shape and tuple(input_shape) != tuple(input_array.shape):
        interpreter.resizeTensor(input_tensor, list(input_array.shape))
        interpreter.resizeSession(session)
        input_tensor = interpreter.getSessionInput(session)

    tmp_input = MNN.Tensor(
        list(input_array.shape),
        MNN.Halide_Type_Float,
        input_array.astype(np.float32),
        MNN.Tensor_DimensionType_Caffe,
    )

    def copy_input_and_run() -> None:
        input_tensor.copyFrom(tmp_input)
        interpreter.runSession(session)

    for _ in range(warmup):
        copy_input_and_run()

    start = time.perf_counter()
    for _ in range(runs):
        copy_input_and_run()
    elapsed_ms = (time.perf_counter() - start) * 1000.0 / max(runs, 1)

    outputs = []
    if hasattr(interpreter, "getSessionOutputAll"):
        output_tensors = interpreter.getSessionOutputAll(session)
        iterator = output_tensors.values() if isinstance(output_tensors, dict) else output_tensors
    else:
        iterator = [interpreter.getSessionOutput(session)]

    for tensor in iterator:
        shape = list(tensor.getShape())
        host = MNN.Tensor(shape, MNN.Halide_Type_Float, np.zeros(shape, dtype=np.float32), MNN.Tensor_DimensionType_Caffe)
        tensor.copyToHostTensor(host)
        outputs.append(np.asarray(host.getData(), dtype=np.float32).reshape(shape))

    return outputs, elapsed_ms


def main() -> None:
    args = parse_args()
    models_dir = resolve_path(args.models_dir, Path.cwd())
    data_yaml = resolve_data_yaml(args.data)
    image_path = resolve_path(args.image, Path.cwd()) if args.image else collect_dataset_image(data_yaml)
    save_dir = resolve_path(args.save_dir, Path.cwd())

    if not image_path.exists():
        raise FileNotFoundError(f"Cannot find image: {image_path}")

    image = Image.open(image_path).convert("RGB")
    input_array, ratio_pad = letterbox(image, args.imgsz)
    models = collect_models(models_dir, args.weights)
    if not models:
        raise FileNotFoundError(f"No ONNX/MNN models found under: {models_dir}")

    rows = []
    print(f"[info] image: {image_path}")
    print(f"[info] input: {tuple(input_array.shape)}")

    for model_name, paths in sorted(models.items()):
        for backend, path in sorted(paths.items()):
            print(f"\n[{backend}] testing {model_name}: {path}", flush=True)
            try:
                if backend == "onnx":
                    outputs, latency_ms = run_onnx(path, input_array, args.providers, args.warmup, args.runs)
                else:
                    outputs, latency_ms = run_mnn(path, input_array, args.mnn_backend, args.mnn_threads, args.warmup, args.runs)

                detections = parse_yolo_output(outputs, args.conf, args.iou, ratio_pad, image.size)
                output_shapes = [list(output.shape) for output in outputs]
                fps = 1000.0 / latency_ms if latency_ms > 0 else None
                print(f"[ok] latency={latency_ms:.2f} ms, fps={fps:.2f}, detections={len(detections)}, outputs={output_shapes}")

                if not args.no_draw:
                    draw_path = save_dir / f"{model_name}_{backend}.jpg"
                    draw_detections(image, detections, draw_path)
                    print(f"[ok] saved: {draw_path}")

                rows.append(
                    {
                        "model": model_name,
                        "backend": backend,
                        "path": str(path),
                        "latency_ms": latency_ms,
                        "fps": fps,
                        "detections": int(len(detections)),
                        "outputs": output_shapes,
                        "status": "ok",
                    }
                )
            except Exception as exc:  # pylint: disable=broad-exception-caught
                print(f"[failed] {type(exc).__name__}: {exc}", flush=True)
                rows.append(
                    {
                        "model": model_name,
                        "backend": backend,
                        "path": str(path),
                        "status": "failed",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )

    save_dir.mkdir(parents=True, exist_ok=True)
    summary_path = save_dir / "summary.json"
    summary_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[ok] summary saved: {summary_path}")


if __name__ == "__main__":
    main()

'''
python ./model-convert/test_exported_models.py \
  --models-dir ./models \
  --data ./datasets/vehicle_flow.yaml \
  --imgsz 960 \
  --conf 0.25 \
  --iou 0.45 \
  --runs 20
'''

