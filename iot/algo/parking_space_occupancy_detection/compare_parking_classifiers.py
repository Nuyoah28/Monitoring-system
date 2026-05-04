from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch
from sklearn.metrics import accuracy_score, classification_report
from sklearn.svm import SVC
from torch import nn
from torch.utils.data import DataLoader, Dataset, Subset
from torchvision import transforms
from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small


ROOT = Path(__file__).resolve().parent
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
CLASS_TO_LABEL = {"empty": 0, "not_empty": 1}
CLASS_NAMES = ["empty", "not_empty"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare SVM and MobileNetV3 on parking crop classification.")
    parser.add_argument("--data", default="../img/parking/clf-data")
    parser.add_argument("--output-json", default="runs/parking_classifier/compare_results.json")
    parser.add_argument("--mobilenet-output", default="../img/parking/model/mobilenetv3_parking.pt")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch", type=int, default=64)
    parser.add_argument("--imgsz", type=int, default=96)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="0")
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--max-per-class", type=int, default=0)
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
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        return None
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def collect_samples(data_dir: Path, max_per_class: int, seed: int) -> list[tuple[Path, int]]:
    samples: list[tuple[Path, int]] = []
    rng = random.Random(seed)
    for class_name, label in CLASS_TO_LABEL.items():
        class_dir = data_dir / class_name
        if not class_dir.exists():
            raise FileNotFoundError(f"Missing class directory: {class_dir}")
        image_paths = sorted(path for path in class_dir.rglob("*") if path.suffix.lower() in IMAGE_SUFFIXES)
        if max_per_class > 0:
            rng.shuffle(image_paths)
            image_paths = image_paths[:max_per_class]
        samples.extend((path, label) for path in image_paths)
    if not samples:
        raise ValueError(f"No images found in: {data_dir}")
    return samples


def split_indices(samples: list[tuple[Path, int]], test_size: float, seed: int) -> tuple[list[int], list[int]]:
    by_label: dict[int, list[int]] = {}
    for index, (_, label) in enumerate(samples):
        by_label.setdefault(label, []).append(index)

    rng = random.Random(seed)
    train_indices: list[int] = []
    val_indices: list[int] = []
    for indices in by_label.values():
        rng.shuffle(indices)
        val_count = max(1, int(round(len(indices) * test_size)))
        val_indices.extend(indices[:val_count])
        train_indices.extend(indices[val_count:])
    rng.shuffle(train_indices)
    rng.shuffle(val_indices)
    return train_indices, val_indices


def svm_feature(path: Path) -> np.ndarray:
    image = read_image(path)
    if image is None:
        raise RuntimeError(f"Cannot read image: {path}")
    resized = cv2.resize(image, (15, 15), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    return resized.flatten()


def train_eval_svm(samples: list[tuple[Path, int]], train_indices: list[int], val_indices: list[int]) -> dict[str, Any]:
    start = time.perf_counter()
    x_train = np.asarray([svm_feature(samples[index][0]) for index in train_indices])
    y_train = np.asarray([samples[index][1] for index in train_indices])
    x_val = np.asarray([svm_feature(samples[index][0]) for index in val_indices])
    y_val = np.asarray([samples[index][1] for index in val_indices])

    model = SVC(kernel="rbf", gamma="scale", C=10)
    model.fit(x_train, y_train)
    train_seconds = time.perf_counter() - start

    start = time.perf_counter()
    pred = model.predict(x_val)
    infer_seconds = time.perf_counter() - start

    return {
        "accuracy": float(accuracy_score(y_val, pred)),
        "report": classification_report(y_val, pred, target_names=CLASS_NAMES, output_dict=True),
        "train_seconds": train_seconds,
        "val_infer_seconds": infer_seconds,
    }


class ParkingCropDataset(Dataset):
    def __init__(self, samples: list[tuple[Path, int]], transform) -> None:
        self.samples = samples
        self.transform = transform

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int):
        image_path, label = self.samples[index]
        image = read_image(image_path)
        if image is None:
            raise RuntimeError(f"Cannot read image: {image_path}")
        return self.transform(image), torch.tensor(label, dtype=torch.long)


def create_mobilenet(num_classes: int) -> nn.Module:
    model = mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.DEFAULT)
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Linear(in_features, num_classes)
    return model


def resolve_device(raw: str) -> torch.device:
    if raw == "cpu" or not torch.cuda.is_available():
        return torch.device("cpu")
    return torch.device(f"cuda:{raw}")


def run_epoch(model, loader, criterion, optimizer, device: torch.device, train: bool) -> tuple[float, float]:
    model.train(train)
    total_loss = 0.0
    total_correct = 0
    total = 0
    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)
        with torch.set_grad_enabled(train):
            logits = model(images)
            loss = criterion(logits, labels)
            if train:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
        total_loss += float(loss.item()) * images.size(0)
        total_correct += int((logits.argmax(dim=1) == labels).sum().item())
        total += images.size(0)
    return total_loss / max(1, total), total_correct / max(1, total)


def predict_mobilenet(model, loader, device: torch.device) -> tuple[list[int], list[int], float]:
    model.eval()
    labels_all: list[int] = []
    preds_all: list[int] = []
    start = time.perf_counter()
    with torch.inference_mode():
        for images, labels in loader:
            images = images.to(device)
            logits = model(images)
            preds_all.extend(int(value) for value in logits.argmax(dim=1).cpu().tolist())
            labels_all.extend(int(value) for value in labels.tolist())
    return labels_all, preds_all, time.perf_counter() - start


def train_eval_mobilenet(
    samples: list[tuple[Path, int]],
    train_indices: list[int],
    val_indices: list[int],
    args: argparse.Namespace,
    output_path: Path,
) -> dict[str, Any]:
    device = resolve_device(args.device)
    train_transform = transforms.Compose(
        [
            transforms.ToPILImage(),
            transforms.Resize((args.imgsz, args.imgsz)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.1),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
    val_transform = transforms.Compose(
        [
            transforms.ToPILImage(),
            transforms.Resize((args.imgsz, args.imgsz)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    train_dataset = Subset(ParkingCropDataset(samples, train_transform), train_indices)
    val_dataset = Subset(ParkingCropDataset(samples, val_transform), val_indices)
    train_loader = DataLoader(train_dataset, batch_size=args.batch, shuffle=True, num_workers=args.workers)
    val_loader = DataLoader(val_dataset, batch_size=args.batch, shuffle=False, num_workers=args.workers)

    model = create_mobilenet(num_classes=len(CLASS_NAMES)).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.0001)

    best_acc = -1.0
    best_state = None
    history = []
    start = time.perf_counter()
    for epoch in range(1, args.epochs + 1):
        train_loss, train_acc = run_epoch(model, train_loader, criterion, optimizer, device, train=True)
        val_loss, val_acc = run_epoch(model, val_loader, criterion, optimizer, device, train=False)
        history.append(
            {
                "epoch": epoch,
                "train_loss": train_loss,
                "train_acc": train_acc,
                "val_loss": val_loss,
                "val_acc": val_acc,
            }
        )
        print(
            f"mobilenet epoch {epoch:03d}/{args.epochs} "
            f"train_acc={train_acc:.4f} val_acc={val_acc:.4f}"
        )
        if val_acc > best_acc:
            best_acc = val_acc
            best_state = {key: value.detach().cpu() for key, value in model.state_dict().items()}
    train_seconds = time.perf_counter() - start

    if best_state is not None:
        model.load_state_dict(best_state)
    labels, preds, infer_seconds = predict_mobilenet(model, val_loader, device)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model": "mobilenet_v3_small",
            "model_state": best_state or model.state_dict(),
            "class_names": CLASS_NAMES,
            "image_size": args.imgsz,
            "best_val_acc": best_acc,
        },
        output_path,
    )

    return {
        "accuracy": float(accuracy_score(labels, preds)),
        "best_val_acc": float(best_acc),
        "report": classification_report(labels, preds, target_names=CLASS_NAMES, output_dict=True),
        "train_seconds": train_seconds,
        "val_infer_seconds": infer_seconds,
        "history": history,
        "saved_model": str(output_path),
        "device": str(device),
    }


def main() -> None:
    args = parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    data_dir = resolve_path(ROOT, args.data)
    output_json = resolve_path(ROOT, args.output_json)
    mobilenet_output = resolve_path(ROOT, args.mobilenet_output)

    samples = collect_samples(data_dir, args.max_per_class, args.seed)
    train_indices, val_indices = split_indices(samples, args.test_size, args.seed)

    print(f"samples={len(samples)} train={len(train_indices)} val={len(val_indices)}")
    svm_result = train_eval_svm(samples, train_indices, val_indices)
    print(f"svm accuracy={svm_result['accuracy']:.4f}")
    mobilenet_result = train_eval_mobilenet(samples, train_indices, val_indices, args, mobilenet_output)
    print(f"mobilenet accuracy={mobilenet_result['accuracy']:.4f}")

    payload = {
        "data_dir": str(data_dir),
        "class_names": CLASS_NAMES,
        "train_samples": len(train_indices),
        "val_samples": len(val_indices),
        "svm": svm_result,
        "mobilenet_v3": mobilenet_result,
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved compare result: {output_json}")


if __name__ == "__main__":
    main()


'''
python ./compare_parking_classifiers.py `
  --data ../img/parking/clf-data `
  --output-json ./runs/parking_classifier/compare_results.json `
  --mobilenet-output ../img/parking/model/mobilenetv3_parking.pt `
  --epochs 5 `
  --batch 64 `
  --device 0
'''
