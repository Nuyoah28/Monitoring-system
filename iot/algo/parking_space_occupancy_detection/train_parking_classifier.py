from __future__ import annotations

import argparse
import random
from pathlib import Path

import cv2
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset, Subset
from torchvision import transforms
from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small


ROOT = Path(__file__).resolve().parent
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
CLASS_TO_LABEL = {"empty": 0, "not_empty": 1}
CLASS_NAMES = ["empty", "not_empty"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train MobileNetV3 empty/not_empty parking classifier.")
    parser.add_argument("--data", default="../img/parking/clf-data", help="Directory containing empty/not_empty folders")
    parser.add_argument("--output", default="../img/parking/model/mobilenetv3_parking.pt", help="Output checkpoint path")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch", type=int, default=64)
    parser.add_argument("--imgsz", type=int, default=96)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="0", help="Device, e.g. 0 or cpu")
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--max-per-class", type=int, default=0, help="Limit samples per class, 0 means all")
    parser.add_argument("--no-pretrained", action="store_true", help="Train MobileNetV3 from scratch")
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
        raise ValueError(f"No training images found in: {data_dir}")
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


def create_model(num_classes: int, pretrained: bool) -> nn.Module:
    if pretrained:
        try:
            model = mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.DEFAULT)
            print("[INFO] using ImageNet pretrained MobileNetV3 weights")
        except Exception as exc:  # pylint: disable=broad-except
            print(f"[WARN] pretrained weights unavailable, training from scratch: {exc}")
            model = mobilenet_v3_small(weights=None)
    else:
        model = mobilenet_v3_small(weights=None)
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


def main() -> None:
    args = parse_args()
    torch.manual_seed(args.seed)
    random.seed(args.seed)

    data_dir = resolve_path(ROOT, args.data)
    output_path = resolve_path(ROOT, args.output)
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

    samples = collect_samples(data_dir, args.max_per_class, args.seed)
    train_indices, val_indices = split_indices(samples, args.test_size, args.seed)
    train_dataset = Subset(ParkingCropDataset(samples, train_transform), train_indices)
    val_dataset = Subset(ParkingCropDataset(samples, val_transform), val_indices)

    train_loader = DataLoader(train_dataset, batch_size=args.batch, shuffle=True, num_workers=args.workers)
    val_loader = DataLoader(val_dataset, batch_size=args.batch, shuffle=False, num_workers=args.workers)

    model = create_model(num_classes=len(CLASS_NAMES), pretrained=not args.no_pretrained).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.0001)

    best_acc = -1.0
    best_state = None
    for epoch in range(1, args.epochs + 1):
        train_loss, train_acc = run_epoch(model, train_loader, criterion, optimizer, device, train=True)
        val_loss, val_acc = run_epoch(model, val_loader, criterion, optimizer, device, train=False)
        print(
            f"epoch {epoch:03d}/{args.epochs} "
            f"train_loss={train_loss:.4f} train_acc={train_acc:.4f} "
            f"val_loss={val_loss:.4f} val_acc={val_acc:.4f}"
        )
        if val_acc > best_acc:
            best_acc = val_acc
            best_state = {key: value.detach().cpu() for key, value in model.state_dict().items()}

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

    print(f"Training samples: {len(train_dataset)}")
    print(f"Validation samples: {len(val_dataset)}")
    print(f"Best val acc: {best_acc:.4f}")
    print(f"Saved model: {output_path}")


if __name__ == "__main__":
    main()


'''
python ./train_parking_classifier.py `
  --data ../img/parking/clf-data `
  --output ../img/parking/model/mobilenetv3_parking.pt `
  --epochs 20 `
  --batch 64 `
  --device 0
'''
