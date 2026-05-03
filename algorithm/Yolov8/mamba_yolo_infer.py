"""Inference helpers for Mamba-YOLO-World.

This module keeps the detector wrapper small by isolating the per-frame data
preparation and result conversion logic.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
import torch


def build_data_batch(test_pipeline, img_src, texts):
    """Build the MMDetection-style batch expected by the detector.

    Text features are already cached on the model by reparameterize(). Passing
    texts through data_samples adds another batch dimension and breaks the
    tokenizer path in this runtime.
    """
    _ = texts
    data_info = dict(img_id=0, img=img_src)
    data_info = test_pipeline(data_info)
    return dict(
        inputs=data_info['inputs'].unsqueeze(0),
        data_samples=[data_info['data_samples']]
    )


def filter_and_limit(pred_instances, confidence: float, max_dets: int):
    """Apply confidence filtering and top-k limiting without changing outputs."""
    pred_instances = pred_instances[pred_instances.scores.float() > confidence]
    if len(pred_instances.scores) > max_dets:
        indices = pred_instances.scores.float().topk(max_dets)[1]
        pred_instances = pred_instances[indices]
    return pred_instances


def to_numpy_outputs(pred_instances) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Convert prediction instances to the legacy detector output format."""
    pred_instances = pred_instances.cpu().numpy()
    if len(pred_instances['bboxes']) == 0:
        empty = np.empty((0,), dtype=np.float32)
        return np.empty((0, 4), dtype=np.float32), empty, empty

    boxes = pred_instances['bboxes'].astype(np.float32)
    scores = pred_instances['scores'].astype(np.float32)
    idxs = pred_instances['labels'].astype(np.int32)
    return boxes, scores, idxs


def run_inference(model, test_pipeline, img_src, texts, confidence: float, max_dets: int):
    """Execute a single-frame inference pass and return legacy outputs."""
    data_batch = build_data_batch(test_pipeline, img_src, texts)
    with torch.no_grad():
        output = model.test_step(data_batch)[0]
        pred_instances = output.pred_instances
        pred_instances = filter_and_limit(pred_instances, confidence=confidence, max_dets=max_dets)
    return to_numpy_outputs(pred_instances)
