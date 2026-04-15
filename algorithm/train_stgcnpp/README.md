# ST-GCN++ Fine-Tune (Server)

This folder contains a lightweight training pipeline for fine-tuning ST-GCN++ on your own classes, while staying compatible with the existing inference code in this project.

## 0) If You Only Have Videos

You need one preprocessing step before training: convert videos into pose sequences (`.npy`).

Input example:

```text
/data/action_videos/
  normal/*.mp4
  fall/*.mp4
  punch/*.mp4
  wave/*.mp4
```

Run extractor:

```bash
cd /path/to/Monitoring-system/algorithm
python train_stgcnpp/extract_pose_sequences.py \
  --input-root /data/action_videos \
  --output-root /data/pose_sequences \
  --pose-engine algo/yolov8n-pose.engine \
  --min-frames 20 \
  --max-frames 120 \
  --frame-step 1
```

Then use `/data/pose_sequences` for manifest generation and training.

## 1) Dataset Format

Prepare pose sequences as `.npy` or `.npz` files under class folders:

```text
your_dataset_root/
  normal/
    xxx.npy
  fall/
    xxx.npy
  punch/      # or fight/ (mapped to punch)
    xxx.npy
  wave/
    xxx.npy
```

Each sequence file can be one of:

- `(T, 17, 3)` preferred
- `(3, T, 17)`
- `(17, 3, T)`
- `(T, 51)`

Where `3 = (x, y, conf)`.

## 2) Build Manifests

```bash
cd /path/to/Monitoring-system/algorithm
python train_stgcnpp/prepare_manifest.py \
  --dataset-root /data/pose_sequences \
  --output-dir /data/pose_manifests \
  --val-ratio 0.2
```

Outputs:

- `train.jsonl`
- `val.jsonl`
- `label_meta.json`

## 3) Train On Server

```bash
cd /path/to/Monitoring-system/algorithm
python train_stgcnpp/train_stgcnpp.py \
  --train-manifest /data/pose_manifests/train.jsonl \
  --val-manifest /data/pose_manifests/val.jsonl \
  --output-dir /data/stgcn_runs/run1 \
  --pretrained algo/stgcnpp_ntu60.pth \
  --epochs 40 \
  --batch-size 16 \
  --clip-len 30 \
  --label-names normal,fall,punch,wave
```

Main outputs:

- `best_stgcnpp_custom.pth`
- `last_stgcnpp_custom.pth`
- `train_history.json`

## 4) Use Trained Weights In Inference

Replace checkpoint path in your runtime config (or code) with:

- `/data/stgcn_runs/run1/best_stgcnpp_custom.pth`

`Yolov8/stgcn_action.py` already supports both:

- legacy NTU-60 checkpoint (60 classes)
- custom checkpoint with `meta.label_names` (e.g. 4 classes)

So no extra inference code rewrite is required.

## 5) Minimal Server Dependencies

```bash
pip install -r train_stgcnpp/requirements_train.txt
```
