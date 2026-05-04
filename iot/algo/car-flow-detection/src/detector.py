from __future__ import annotations

import sys
from pathlib import Path

from .geometry import bottom_center
from .models import TrackedObject
from .single_class_dataset import VEHICLE_CLASS_ID, VEHICLE_CLASS_NAME


class LocalYoloTracker:
    def __init__(
        self,
        model_path: str,
        tracker_path: str,
        conf: float = 0.25,
        iou: float = 0.5,
        imgsz: int = 640,
        device: str = "cpu",
        max_det: int = 300,
        half: bool = False,
        verbose: bool = False,
    ) -> None:
        self.conf = conf
        self.iou = iou
        self.imgsz = imgsz
        self.device = device
        self.max_det = max_det
        self.half = half
        self.verbose = verbose
        self.tracker_path = str(Path(tracker_path).resolve())
        self.model = self._load_model(model_path)

    def _load_model(self, model_path: str):
        carflow_root = Path(__file__).resolve().parents[1]
        ultralytics_root = carflow_root / "yolov13-lite"
        ultralytics_root = ultralytics_root.resolve()
        if not ultralytics_root.exists():
            raise FileNotFoundError(f"Cannot find local ultralytics fork: {ultralytics_root}")

        if str(ultralytics_root) not in sys.path:
            sys.path.insert(0, str(ultralytics_root))

        from ultralytics import YOLO  # pylint: disable=import-error,import-outside-toplevel

        resolved_model_path = Path(model_path).expanduser().resolve()
        if not resolved_model_path.exists():
            raise FileNotFoundError(f"Cannot find model weights/config: {resolved_model_path}")

        model = YOLO(str(resolved_model_path))
        return model

    def track(self, frame) -> list[TrackedObject]:
        results = self.model.track(
            source=frame,
            persist=True,
            tracker=self.tracker_path,
            classes=[VEHICLE_CLASS_ID],
            conf=self.conf,
            iou=self.iou,
            imgsz=self.imgsz,
            device=self.device,
            max_det=self.max_det,
            half=self.half,
            verbose=self.verbose,
        )

        if not results:
            return []

        result = results[0]
        boxes = result.obb or result.boxes
        if boxes is None or boxes.id is None:
            return []

        xyxy = boxes.xyxy.cpu().tolist()
        track_ids = [int(value) for value in boxes.id.int().cpu().tolist()]
        confidences = boxes.conf.cpu().tolist() if boxes.conf is not None else [1.0] * len(track_ids)

        tracked_objects: list[TrackedObject] = []
        for bbox, track_id, confidence in zip(xyxy, track_ids, confidences):
            anchor = bottom_center(bbox)
            tracked_objects.append(
                TrackedObject(
                    track_id=track_id,
                    class_id=VEHICLE_CLASS_ID,
                    class_name=VEHICLE_CLASS_NAME,
                    confidence=float(confidence),
                    bbox=tuple(float(value) for value in bbox),
                    anchor=anchor,
                )
            )
        return tracked_objects
