from pathlib import Path

from ultralytics.engine.model import Model
from ultralytics.models import yolo
from ultralytics.nn.tasks import ClassificationModel, DetectionModel, OBBModel, PoseModel, SegmentationModel, WorldModel
from ultralytics.utils import ROOT, yaml_load


class YOLO(Model):
    """YOLO detection model entry for this trimmed YOLOv13-lite tree."""

    def __init__(self, model="yolo11n.pt", task=None, verbose=False):
        path = Path(model)
        if "-world" in path.stem and path.suffix in {".pt", ".yaml", ".yml"}:
            new_instance = YOLOWorld(path, verbose=verbose)
            self.__class__ = type(new_instance)
            self.__dict__ = new_instance.__dict__
        else:
            super().__init__(model=model, task=task, verbose=verbose)

    @property
    def task_map(self):
        return {
            "classify": {
                "model": ClassificationModel,
                "trainer": yolo.classify.ClassificationTrainer,
                "validator": yolo.classify.ClassificationValidator,
                "predictor": yolo.classify.ClassificationPredictor,
            },
            "detect": {
                "model": DetectionModel,
                "trainer": yolo.detect.DetectionTrainer,
                "validator": yolo.detect.DetectionValidator,
                "predictor": yolo.detect.DetectionPredictor,
            },
            "segment": {
                "model": SegmentationModel,
                "trainer": yolo.segment.SegmentationTrainer,
                "validator": yolo.segment.SegmentationValidator,
                "predictor": yolo.segment.SegmentationPredictor,
            },
            "pose": {
                "model": PoseModel,
                "trainer": yolo.pose.PoseTrainer,
                "validator": yolo.pose.PoseValidator,
                "predictor": yolo.pose.PosePredictor,
            },
            "obb": {
                "model": OBBModel,
                "trainer": yolo.obb.OBBTrainer,
                "validator": yolo.obb.OBBValidator,
                "predictor": yolo.obb.OBBPredictor,
            },
        }


class YOLOWorld(Model):
    """YOLO-World entry kept for import compatibility."""

    def __init__(self, model="yolov8s-world.pt", verbose=False) -> None:
        super().__init__(model=model, task="detect", verbose=verbose)
        if not hasattr(self.model, "names"):
            self.model.names = yaml_load(ROOT / "cfg/datasets/coco8.yaml").get("names")

    @property
    def task_map(self):
        return {
            "detect": {
                "model": WorldModel,
                "validator": yolo.detect.DetectionValidator,
                "predictor": yolo.detect.DetectionPredictor,
                "trainer": yolo.world.WorldTrainer,
            }
        }

    def set_classes(self, classes):
        self.model.set_classes(classes)
        background = " "
        if background in classes:
            classes.remove(background)
        self.model.names = classes
        if self.predictor:
            self.predictor.model.names = classes
