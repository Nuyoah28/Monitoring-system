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

from parking_classifier_lib import (
    CLASS_NAMES,
    DEFAULT_MODELS,
    ROOT,
    build_dataloaders,
    checkpoint_default_output,
    create_model,
    load_dataset_splits,
    predict_model,
    read_image,
    resolve_device,
    resolve_path,
    run_epoch,
    save_checkpoint,
    summarize_splits,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare multiple parking occupancy classifiers on one dataset.")
    parser.add_argument("--data", default="../img/parking/archive (1)")
    parser.add_argument("--dataset-type", default="auto", choices=["auto", "flat", "cnr_ext", "cnrpark"])
    parser.add_argument("--models", default=",".join(DEFAULT_MODELS))
    parser.add_argument("--output-json", default="runs/parking_classifier/compare_results_v2.json")
    parser.add_argument("--checkpoint-dir", default="runs/parking_classifier/models")
    parser.add_argument("--summary-md", default="runs/parking_classifier/compare_summary.md")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch", type=int, default=64)
    parser.add_argument("--imgsz", type=int, default=160)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--val-size", type=float, default=0.2)
    parser.add_argument("--test-size", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="0")
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--max-per-class", type=int, default=0)
    parser.add_argument("--max-samples-per-split", type=int, default=0)
    parser.add_argument("--no-pretrained", action="store_true")
    parser.add_argument("--include-svm", action="store_true")
    return parser.parse_args()


def svm_feature(path: Path) -> np.ndarray:
    image = read_image(path)
    if image is None:
        raise RuntimeError(f"Cannot read image: {path}")
    resized = cv2.resize(image, (15, 15), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    return resized.flatten()


def train_eval_svm(split_samples: dict[str, list], eval_split: str) -> dict[str, Any]:
    train_samples = split_samples["train"]
    eval_samples = split_samples[eval_split]

    start = time.perf_counter()
    x_train = np.asarray([svm_feature(sample.path) for sample in train_samples])
    y_train = np.asarray([sample.label for sample in train_samples])
    x_eval = np.asarray([svm_feature(sample.path) for sample in eval_samples])
    y_eval = np.asarray([sample.label for sample in eval_samples])

    model = SVC(kernel="rbf", gamma="scale", C=10)
    model.fit(x_train, y_train)
    train_seconds = time.perf_counter() - start

    start = time.perf_counter()
    pred = model.predict(x_eval)
    infer_seconds = time.perf_counter() - start

    return {
        "accuracy": float(accuracy_score(y_eval, pred)),
        "report": classification_report(y_eval, pred, target_names=CLASS_NAMES, output_dict=True, zero_division=0),
        "train_seconds": train_seconds,
        "eval_infer_seconds": infer_seconds,
        "eval_split": eval_split,
    }


def train_eval_model(
    model_name: str,
    split_samples: dict[str, list],
    args: argparse.Namespace,
    checkpoint_dir: Path,
) -> dict[str, Any]:
    device = resolve_device(args.device)
    loaders = build_dataloaders(split_samples, imgsz=args.imgsz, batch_size=args.batch, workers=args.workers)
    model, model_meta = create_model(
        model_name=model_name,
        num_classes=len(CLASS_NAMES),
        pretrained=not args.no_pretrained,
    )
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.0001)

    best_acc = -1.0
    best_state = None
    history = []
    start = time.perf_counter()
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
            f"{model_name} epoch {epoch:03d}/{args.epochs} "
            f"train_acc={train_acc:.4f} val_acc={val_acc:.4f}"
        )
        if val_acc > best_acc:
            best_acc = val_acc
            best_state = {key: value.detach().cpu() for key, value in model.state_dict().items()}
    train_seconds = time.perf_counter() - start

    if best_state is not None:
        model.load_state_dict(best_state)

    eval_split = "test" if "test" in loaders and len(split_samples["test"]) > 0 else "val"
    labels, preds, infer_seconds = predict_model(model, loaders[eval_split], device)

    output_path = checkpoint_dir / f"{model_name}.pt"
    save_checkpoint(
        output_path=output_path,
        model_name=model_name,
        model_state=best_state or model.state_dict(),
        image_size=args.imgsz,
        best_val_acc=float(best_acc),
        extra={
            "dataset_type": args.dataset_type,
            "eval_split": eval_split,
            "pretrained_used": model_meta.get("pretrained_used", False),
            "split_summary": summarize_splits(split_samples),
        },
    )

    return {
        "accuracy": float(accuracy_score(labels, preds)),
        "best_val_acc": float(best_acc),
        "report": classification_report(labels, preds, target_names=CLASS_NAMES, output_dict=True, zero_division=0),
        "train_seconds": train_seconds,
        "eval_infer_seconds": infer_seconds,
        "history": history,
        "saved_model": str(output_path),
        "device": str(device),
        "eval_split": eval_split,
        "pretrained_used": model_meta.get("pretrained_used", False),
    }


def write_summary_markdown(summary_path: Path, results: dict[str, Any]) -> None:
    lines = ["# Parking Classifier Comparison", ""]
    lines.append(f"- dataset: `{results['data_dir']}`")
    lines.append(f"- dataset_type: `{results['dataset_type']}`")
    lines.append(f"- split_summary: `{results['split_summary']}`")
    lines.append("")
    lines.append("| Model | Accuracy | Best Val Acc | Train Seconds | Eval Seconds | Eval Split | Pretrained Used |")
    lines.append("| --- | ---: | ---: | ---: | ---: | --- | --- |")
    for model_name, metrics in results.get("models", {}).items():
        lines.append(
            f"| {model_name} | {metrics['accuracy']:.4f} | {metrics['best_val_acc']:.4f} | "
            f"{metrics['train_seconds']:.2f} | {metrics['eval_infer_seconds']:.2f} | "
            f"{metrics['eval_split']} | {metrics.get('pretrained_used', False)} |"
        )
    if "svm" in results:
        svm = results["svm"]
        lines.append(
            f"| svm | {svm['accuracy']:.4f} | - | {svm['train_seconds']:.2f} | "
            f"{svm['eval_infer_seconds']:.2f} | {svm['eval_split']} | - |"
        )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    data_dir = resolve_path(ROOT, args.data)
    output_json = resolve_path(ROOT, args.output_json)
    checkpoint_dir = resolve_path(ROOT, args.checkpoint_dir)
    summary_md = resolve_path(ROOT, args.summary_md)

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
    print(f"[INFO] split_summary={split_summary}")

    models = [item.strip() for item in args.models.split(",") if item.strip()]
    if not models:
        raise ValueError("No models provided.")

    payload: dict[str, Any] = {
        "data_dir": str(data_dir),
        "dataset_type": args.dataset_type,
        "class_names": CLASS_NAMES,
        "split_summary": split_summary,
        "models": {},
    }

    for model_name in models:
        print(f"[INFO] training {model_name}")
        payload["models"][model_name] = train_eval_model(model_name, split_samples, args, checkpoint_dir)
        print(f"[INFO] {model_name} accuracy={payload['models'][model_name]['accuracy']:.4f}")

    if args.include_svm:
        eval_split = "test" if "test" in split_samples and split_samples["test"] else "val"
        payload["svm"] = train_eval_svm(split_samples, eval_split)
        print(f"[INFO] svm accuracy={payload['svm']['accuracy']:.4f}")

    best_name = max(payload["models"], key=lambda name: payload["models"][name]["accuracy"])
    payload["recommended_model"] = {
        "name": best_name,
        "accuracy": payload["models"][best_name]["accuracy"],
        "saved_model": payload["models"][best_name]["saved_model"],
        "default_output": str(resolve_path(ROOT, checkpoint_default_output(best_name))),
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_summary_markdown(summary_md, payload)
    print(f"[INFO] saved compare result: {output_json}")
    print(f"[INFO] saved summary markdown: {summary_md}")


if __name__ == "__main__":
    main()
