import argparse
import json
import math
import os
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

from Yolov8.stgcn_action import STGCN


def parse_args():
    parser = argparse.ArgumentParser(description="Train ST-GCN++ for custom action classes.")
    parser.add_argument("--train-manifest", required=True, help="Path to train.jsonl")
    parser.add_argument("--val-manifest", required=True, help="Path to val.jsonl")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument(
        "--pretrained",
        default="",
        help="Optional pretrained checkpoint (e.g. algo/stgcnpp_ntu60.pth)",
    )
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--clip-len", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="cuda")
    parser.add_argument(
        "--label-names",
        default="normal,fall,punch,wave",
        help="Comma-separated class names aligned with label id.",
    )
    return parser.parse_args()


def set_seed(seed):
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def load_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def load_sequence(path):
    path = str(path)
    if path.endswith(".npz"):
        data = np.load(path)
        if "keypoints" in data:
            arr = data["keypoints"]
        elif "data" in data:
            arr = data["data"]
        else:
            keys = list(data.keys())
            if not keys:
                raise ValueError(f"npz has no arrays: {path}")
            arr = data[keys[0]]
    else:
        arr = np.load(path)
    return np.asarray(arr, dtype=np.float32)


def normalize_to_tvc(arr):
    """
    Convert sequence to shape (T, 17, 3).
    Supported:
      - (T, 17, 3)
      - (3, T, 17)
      - (17, 3, T)
      - (T, 51)
    """
    if arr.ndim == 3 and arr.shape[1:] == (17, 3):
        return arr
    if arr.ndim == 3 and arr.shape[0] == 3 and arr.shape[2] == 17:
        return arr.transpose(1, 2, 0)
    if arr.ndim == 3 and arr.shape[0] == 17 and arr.shape[1] == 3:
        return arr.transpose(2, 0, 1)
    if arr.ndim == 2 and arr.shape[1] == 51:
        return arr.reshape(arr.shape[0], 17, 3)
    raise ValueError(f"Unsupported keypoint array shape: {arr.shape}")


def temporal_fix_length(tvc, clip_len, train_mode):
    t = tvc.shape[0]
    if t == clip_len:
        return tvc
    if t > clip_len:
        if train_mode:
            start = np.random.randint(0, t - clip_len + 1)
        else:
            start = (t - clip_len) // 2
        return tvc[start:start + clip_len]
    # pad to clip_len by repeating last frame
    pad = np.repeat(tvc[-1:, :, :], clip_len - t, axis=0)
    return np.concatenate([tvc, pad], axis=0)


def normalize_pose_sequence(tvc):
    """
    Person-centric normalization per frame.
    tvc: (T,17,3) -> normalized (T,17,3)
    """
    out = tvc.astype(np.float32).copy()
    for t in range(out.shape[0]):
        kp = out[t]
        vis = kp[:, 2] > 0.05
        if np.sum(vis) < 2:
            continue
        xy = kp[vis, :2]
        center = xy.mean(axis=0)
        span = xy.max(axis=0) - xy.min(axis=0)
        scale = float(max(span[0], span[1], 1e-3))
        out[t, :, 0] = (out[t, :, 0] - center[0]) / scale
        out[t, :, 1] = (out[t, :, 1] - center[1]) / scale
    return out


class PoseSequenceDataset(Dataset):
    def __init__(self, manifest_path, clip_len, train_mode=False):
        self.samples = load_jsonl(manifest_path)
        if not self.samples:
            raise RuntimeError(f"empty manifest: {manifest_path}")
        self.clip_len = clip_len
        self.train_mode = train_mode

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        row = self.samples[idx]
        seq_path = row["sequence_path"]
        label = int(row["label"])

        arr = load_sequence(seq_path)
        tvc = normalize_to_tvc(arr)
        tvc = temporal_fix_length(tvc, self.clip_len, self.train_mode)  # (T,17,3)
        tvc = normalize_pose_sequence(tvc)

        # mild train-time noise for robustness
        if self.train_mode:
            noise = np.random.normal(0.0, 0.003, size=tvc.shape).astype(np.float32)
            tvc = tvc + noise

        ctv = tvc.transpose(2, 0, 1)  # (3,T,17)
        x = torch.from_numpy(ctv).float().unsqueeze(-1)  # (3,T,17,1)
        y = torch.tensor(label, dtype=torch.long)
        return x, y


def build_model(num_classes, pretrained_ckpt):
    model = STGCN(in_channels=3, num_classes=num_classes)
    if not pretrained_ckpt:
        return model

    if not os.path.exists(pretrained_ckpt):
        print(f"[WARN] pretrained not found: {pretrained_ckpt}")
        return model

    ckpt = torch.load(pretrained_ckpt, map_location="cpu")
    if isinstance(ckpt, dict) and "state_dict" in ckpt:
        ckpt = ckpt["state_dict"]

    cleaned = {}
    for k, v in ckpt.items():
        new_key = k.replace("backbone.", "").replace("cls_head.", "")
        cleaned[new_key] = v

    # Do not load classifier head when class count is different.
    if "fc_cls.weight" in cleaned and cleaned["fc_cls.weight"].shape[0] != num_classes:
        cleaned.pop("fc_cls.weight", None)
        cleaned.pop("fc_cls.bias", None)

    missing, unexpected = model.load_state_dict(cleaned, strict=False)
    print(f"[INFO] load pretrained: {pretrained_ckpt}")
    if missing:
        print(f"[INFO] missing keys: {missing[:5]}{' ...' if len(missing) > 5 else ''}")
    if unexpected:
        print(f"[INFO] unexpected keys: {unexpected[:5]}{' ...' if len(unexpected) > 5 else ''}")
    return model


def evaluate(model, loader, device, num_classes):
    model.eval()
    total = 0
    correct = 0
    loss_sum = 0.0
    conf = np.zeros((num_classes, num_classes), dtype=np.int64)
    ce = nn.CrossEntropyLoss()
    with torch.no_grad():
        for x, y in loader:
            x = x.to(device, non_blocking=True)
            y = y.to(device, non_blocking=True)
            logits = model(x)
            loss = ce(logits, y)
            loss_sum += loss.item() * x.size(0)
            pred = logits.argmax(dim=1)
            total += x.size(0)
            correct += (pred == y).sum().item()
            for t, p in zip(y.cpu().numpy().tolist(), pred.cpu().numpy().tolist()):
                conf[t, p] += 1

    acc = correct / max(total, 1)
    precision = []
    recall = []
    f1 = []
    for i in range(num_classes):
        tp = conf[i, i]
        fp = conf[:, i].sum() - tp
        fn = conf[i, :].sum() - tp
        p = tp / max(tp + fp, 1)
        r = tp / max(tp + fn, 1)
        if p + r <= 1e-12:
            s = 0.0
        else:
            s = 2 * p * r / (p + r)
        precision.append(p)
        recall.append(r)
        f1.append(s)
    macro_f1 = float(np.mean(f1))
    return {
        "loss": loss_sum / max(total, 1),
        "acc": acc,
        "macro_f1": macro_f1,
    }


def main():
    args = parse_args()
    set_seed(args.seed)

    train_manifest = Path(args.train_manifest).resolve()
    val_manifest = Path(args.val_manifest).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    label_names = [x.strip().lower() for x in args.label_names.split(",") if x.strip()]
    if not label_names:
        raise ValueError("empty --label-names")
    num_classes = len(label_names)

    if not train_manifest.exists():
        raise FileNotFoundError(f"train manifest not found: {train_manifest}")
    if not val_manifest.exists():
        raise FileNotFoundError(f"val manifest not found: {val_manifest}")

    device = args.device
    if device.startswith("cuda") and not torch.cuda.is_available():
        device = "cpu"
    print(f"[INFO] device={device}")
    print(f"[INFO] classes={label_names}")

    train_ds = PoseSequenceDataset(train_manifest, clip_len=args.clip_len, train_mode=True)
    val_ds = PoseSequenceDataset(val_manifest, clip_len=args.clip_len, train_mode=False)
    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=(device != "cpu"),
        drop_last=False,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=(device != "cpu"),
        drop_last=False,
    )

    model = build_model(num_classes=num_classes, pretrained_ckpt=args.pretrained)
    model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scaler = torch.cuda.amp.GradScaler(enabled=(device != "cpu"))
    ce = nn.CrossEntropyLoss()

    best_metric = -math.inf
    history = []

    for epoch in range(1, args.epochs + 1):
        model.train()
        loss_sum = 0.0
        total = 0
        correct = 0

        for x, y in train_loader:
            x = x.to(device, non_blocking=True)
            y = y.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)

            with torch.cuda.amp.autocast(enabled=(device != "cpu")):
                logits = model(x)
                loss = ce(logits, y)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            loss_sum += loss.item() * x.size(0)
            pred = logits.argmax(dim=1)
            total += x.size(0)
            correct += (pred == y).sum().item()

        train_loss = loss_sum / max(total, 1)
        train_acc = correct / max(total, 1)
        val_metrics = evaluate(model, val_loader, device, num_classes)

        row = {
            "epoch": epoch,
            "train_loss": train_loss,
            "train_acc": train_acc,
            "val_loss": val_metrics["loss"],
            "val_acc": val_metrics["acc"],
            "val_macro_f1": val_metrics["macro_f1"],
        }
        history.append(row)
        print(
            f"[E{epoch:03d}] train_loss={train_loss:.4f} train_acc={train_acc:.4f} "
            f"val_loss={val_metrics['loss']:.4f} val_acc={val_metrics['acc']:.4f} "
            f"val_f1={val_metrics['macro_f1']:.4f}"
        )

        # Prefer macro F1 for imbalanced action data.
        score = val_metrics["macro_f1"]
        if score > best_metric:
            best_metric = score
            ckpt_path = output_dir / "best_stgcnpp_custom.pth"
            torch.save(
                {
                    "state_dict": model.state_dict(),
                    "meta": {
                        "label_names": label_names,
                        "clip_len": args.clip_len,
                        "num_classes": num_classes,
                    },
                    "best_val_macro_f1": best_metric,
                    "epoch": epoch,
                },
                ckpt_path,
            )
            print(f"[INFO] saved best checkpoint: {ckpt_path}")

    last_ckpt = output_dir / "last_stgcnpp_custom.pth"
    torch.save(
        {
            "state_dict": model.state_dict(),
            "meta": {
                "label_names": label_names,
                "clip_len": args.clip_len,
                "num_classes": num_classes,
            },
            "best_val_macro_f1": best_metric,
            "epoch": args.epochs,
        },
        last_ckpt,
    )

    history_path = output_dir / "train_history.json"
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    print(f"[INFO] saved last checkpoint: {last_ckpt}")
    print(f"[INFO] saved history: {history_path}")


if __name__ == "__main__":
    main()
