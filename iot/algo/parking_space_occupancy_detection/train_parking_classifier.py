from __future__ import annotations

import argparse
import random
import time
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import accuracy_score, classification_report
from torch import nn

from parking_classifier_lib import (
    CLASS_NAMES,
    ROOT,
    build_dataloaders,
    checkpoint_default_output,
    create_model,
    load_dataset_splits,
    predict_model,
    resolve_device,
    resolve_path,
    run_epoch,
    save_checkpoint,
    summarize_splits,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a parking occupancy classifier with configurable backbones.")
    parser.add_argument("--data", default="../img/parking/archive (1)", help="Dataset root")
    parser.add_argument("--dataset-type", default="auto", choices=["auto", "flat", "cnr_ext", "cnrpark"])
    parser.add_argument("--model", default="mobilenet_v4_small_custom")
    parser.add_argument("--output", default="", help="Checkpoint path; defaults to a model-based path")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch", type=int, default=64)
    parser.add_argument("--imgsz", type=int, default=160)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--val-size", type=float, default=0.2, help="Used by flat/cnrpark datasets")
    parser.add_argument("--test-size", type=float, default=0.0, help="Used by flat/cnrpark datasets")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="0", help="Device, e.g. 0 or cpu")
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--max-per-class", type=int, default=0, help="Limit samples per class per split")
    parser.add_argument("--max-samples-per-split", type=int, default=0, help="Limit split size for CNR-EXT")
    parser.add_argument("--no-pretrained", action="store_true", help="Disable pretrained weights when available")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    random.seed(args.seed)

    data_dir = resolve_path(ROOT, args.data)
    output_path = (
        resolve_path(ROOT, args.output)
        if args.output
        else resolve_path(ROOT, checkpoint_default_output(args.model))
    )
    device = resolve_device(args.device)

    split_samples = load_dataset_splits(
        data_dir=data_dir,
        dataset_type=args.dataset_type,
        seed=args.seed,
        val_size=args.val_size,
        test_size=args.test_size,
        max_per_class=args.max_per_class,
        max_samples_per_split=args.max_samples_per_split,
    )
    split_summary = summarize_splits(split_samples)
    print(f"[INFO] dataset={data_dir}")
    print(f"[INFO] splits={split_summary}")

    loaders = build_dataloaders(
        split_samples=split_samples,
        imgsz=args.imgsz,
        batch_size=args.batch,
        workers=args.workers,
    )

    model, model_meta = create_model(
        model_name=args.model,
        num_classes=len(CLASS_NAMES),
        pretrained=not args.no_pretrained,
    )
    model = model.to(device)
    print(
        f"[INFO] model={args.model} device={device} "
        f"pretrained_used={model_meta.get('pretrained_used', False)}"
    )

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.0001)

    best_acc = -1.0
    best_state = None
    history = []
    train_start = time.perf_counter()
    for epoch in range(1, args.epochs + 1):
        train_loss, train_acc = run_epoch(model, loaders["train"], criterion, optimizer, device, train=True)
        val_loss, val_acc = run_epoch(model, loaders["val"], criterion, optimizer, device, train=False)
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
            f"epoch {epoch:03d}/{args.epochs} "
            f"train_loss={train_loss:.4f} train_acc={train_acc:.4f} "
            f"val_loss={val_loss:.4f} val_acc={val_acc:.4f}"
        )
        if val_acc > best_acc:
            best_acc = val_acc
            best_state = {key: value.detach().cpu() for key, value in model.state_dict().items()}
    train_seconds = time.perf_counter() - train_start

    if best_state is not None:
        model.load_state_dict(best_state)

    eval_split = "test" if "test" in loaders and len(split_samples["test"]) > 0 else "val"
    labels, preds, infer_seconds = predict_model(model, loaders[eval_split], device)
    accuracy = float(accuracy_score(labels, preds))
    report = classification_report(labels, preds, target_names=CLASS_NAMES, output_dict=True, zero_division=0)

    save_checkpoint(
        output_path=output_path,
        model_name=args.model,
        model_state=best_state or model.state_dict(),
        image_size=args.imgsz,
        best_val_acc=float(best_acc),
        extra={
            "dataset_type": args.dataset_type,
            "split_summary": split_summary,
            "eval_split": eval_split,
            "pretrained_used": model_meta.get("pretrained_used", False),
        },
    )

    print(f"[INFO] train_seconds={train_seconds:.2f}")
    print(f"[INFO] eval_split={eval_split} accuracy={accuracy:.4f} infer_seconds={infer_seconds:.2f}")
    print(f"[INFO] saved_model={output_path}")
    print(f"[INFO] report={report['accuracy']:.4f}")


if __name__ == "__main__":
    main()
