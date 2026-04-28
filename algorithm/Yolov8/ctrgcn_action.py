import os
import sys
from collections import deque

import numpy as np
import torch
import torch.nn.functional as F

from common import monitor as monitorCommon
from Yolov8.action_fsm import ActionFSMConfig, TrackActionFSM


def _resolve_ctrgcn_root(explicit_root=None):
    candidates = [
        explicit_root,
        getattr(monitorCommon, "ACTION_CTR_GCN_ROOT", ""),
        os.environ.get("ACTION_CTR_GCN_ROOT", ""),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "CTR-GCN")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "third_party", "CTR-GCN")),
    ]
    for root in candidates:
        if not root:
            continue
        model_file = os.path.join(root, "model", "ctrgcn.py")
        if os.path.isfile(model_file):
            return os.path.abspath(root)
    raise FileNotFoundError(
        "CTR-GCN repo not found. Set ACTION_CTR_GCN_ROOT in env or common/monitor.py."
    )


def _load_ctrgcn_model(ctrgcn_root, weights_path, device, num_class=4, num_point=17, num_person=2):
    if ctrgcn_root not in sys.path:
        sys.path.insert(0, ctrgcn_root)

    from model.ctrgcn import Model

    model = Model(
        num_class=num_class,
        num_point=num_point,
        num_person=num_person,
        graph="graph.action4_coco17.Graph",
        graph_args={"labeling_mode": "spatial"},
    )

    ckpt = torch.load(weights_path, map_location=device)
    state = ckpt["state_dict"] if isinstance(ckpt, dict) and "state_dict" in ckpt else ckpt
    clean = {}
    for key, value in state.items():
        clean[key[7:] if key.startswith("module.") else key] = value

    missing, unexpected = model.load_state_dict(clean, strict=False)
    if missing:
        print(f"[CTR-GCN] missing keys: {len(missing)}")
    if unexpected:
        print(f"[CTR-GCN] unexpected keys: {len(unexpected)}")

    model.to(device).eval()
    return model


class ActionRecognizer:
    def __init__(
        self,
        checkpoint_path,
        ctrgcn_root="",
        label_order=None,
        buffer_size=90,
        min_frames=8,
        smooth=4,
        device=None,
        max_tracks=8,
        top_k_tracks=4,
        infer_interval=1,
        max_missing=10,
    ):
        self.device = torch.device(device or ("cuda:0" if torch.cuda.is_available() else "cpu"))
        self.label_order = tuple(label_order or ("normal", "fall", "punch", "wave"))
        self.label_to_idx = {name: idx for idx, name in enumerate(self.label_order)}
        self.buffer_size = int(buffer_size)
        self.min_frames = int(min_frames)
        self.smooth = max(1, int(smooth))
        self.max_tracks = int(max_tracks)
        self.top_k_tracks = int(top_k_tracks)
        self.infer_interval = max(1, int(infer_interval))
        self.max_missing = int(max_missing)
        self.frame_idx = 0
        self.next_track_id = 1

        self.track_buffers = {}
        self.track_boxes = {}
        self.track_last_seen = {}
        self.track_last_probs = {}
        self.track_last_result = {}
        self.prob_hist = {}
        self.last_result = {"fall": False, "punch": False, "wave": False}
        self.last_overlays = []

        self.ctrgcn_root = _resolve_ctrgcn_root(ctrgcn_root)
        if not os.path.isfile(checkpoint_path):
            raise FileNotFoundError(f"CTR-GCN weight file not found: {checkpoint_path}")
        self.model = _load_ctrgcn_model(
            self.ctrgcn_root,
            checkpoint_path,
            self.device,
            num_class=len(self.label_order),
        )
        self.fsm = TrackActionFSM(
            ActionFSMConfig(
                fall_on_thr=monitorCommon.ACTION_FALL_ON_THR,
                fall_off_thr=monitorCommon.ACTION_FALL_OFF_THR,
                fall_hold_frames=monitorCommon.ACTION_FALL_HOLD_FRAMES,
                fall_release_frames=monitorCommon.ACTION_FALL_RELEASE_FRAMES,
                wave_on_thr=monitorCommon.ACTION_WAVE_ON_THR,
                wave_off_thr=monitorCommon.ACTION_WAVE_OFF_THR,
                wave_confirm_frames=monitorCommon.ACTION_WAVE_CONFIRM_FRAMES,
                wave_release_frames=monitorCommon.ACTION_WAVE_RELEASE_FRAMES,
                punch_on_thr=monitorCommon.ACTION_PUNCH_ON_THR,
                punch_off_thr=monitorCommon.ACTION_PUNCH_OFF_THR,
                punch_confirm_frames=monitorCommon.ACTION_PUNCH_CONFIRM_FRAMES,
                punch_release_frames=monitorCommon.ACTION_PUNCH_RELEASE_FRAMES,
                fight_confirm_frames=monitorCommon.ACTION_FIGHT_CONFIRM_FRAMES,
                fight_release_frames=monitorCommon.ACTION_FIGHT_RELEASE_FRAMES,
                fight_distance_ratio=monitorCommon.ACTION_FIGHT_DISTANCE_RATIO,
            )
        )

        print("[CTR-GCN] model loaded")
        print(f"   root: {self.ctrgcn_root}")
        print(f"   weights: {checkpoint_path}")
        print(f"   labels: {self.label_order}")
        print(f"   buffer={self.buffer_size} min_frames={self.min_frames} smooth={self.smooth}")

    @staticmethod
    def _iou(box_a, box_b):
        xa1, ya1, xa2, ya2 = box_a
        xb1, yb1, xb2, yb2 = box_b
        inter_x1 = max(xa1, xb1)
        inter_y1 = max(ya1, yb1)
        inter_x2 = min(xa2, xb2)
        inter_y2 = min(ya2, yb2)
        iw = max(0.0, inter_x2 - inter_x1)
        ih = max(0.0, inter_y2 - inter_y1)
        inter = iw * ih
        if inter <= 0:
            return 0.0
        area_a = max(0.0, xa2 - xa1) * max(0.0, ya2 - ya1)
        area_b = max(0.0, xb2 - xb1) * max(0.0, yb2 - yb1)
        denom = area_a + area_b - inter
        return inter / denom if denom > 1e-6 else 0.0

    @staticmethod
    def _bbox_area(box):
        return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])

    @staticmethod
    def _box_center(box):
        return np.array([(box[0] + box[2]) * 0.5, (box[1] + box[3]) * 0.5], dtype=np.float32)

    def _assign_tracks(self, bboxes, iou_threshold=0.3):
        det_count = len(bboxes)
        assigned = [-1] * det_count
        if det_count == 0:
            return assigned

        track_ids = list(self.track_boxes.keys())
        if not track_ids:
            return assigned

        pairs = []
        for det_idx, box in enumerate(bboxes):
            for track_id in track_ids:
                iou = self._iou(box, self.track_boxes[track_id])
                if iou >= iou_threshold:
                    pairs.append((iou, det_idx, track_id))

        pairs.sort(reverse=True, key=lambda item: item[0])
        used_det = set()
        used_track = set()
        for _, det_idx, track_id in pairs:
            if det_idx in used_det or track_id in used_track:
                continue
            assigned[det_idx] = track_id
            used_det.add(det_idx)
            used_track.add(track_id)
        return assigned

    def _new_track(self, box):
        track_id = self.next_track_id
        self.next_track_id += 1
        self.track_buffers[track_id] = deque(maxlen=self.buffer_size)
        self.track_boxes[track_id] = box.astype(np.float32)
        self.track_last_seen[track_id] = self.frame_idx
        self.track_last_probs[track_id] = np.zeros((len(self.label_order),), dtype=np.float32)
        self.track_last_result[track_id] = {
            "fall": False,
            "punch": False,
            "wave": False,
            "fall_prob": 0.0,
            "wave_prob": 0.0,
            "punch_prob": 0.0,
        }
        self.prob_hist[track_id] = deque(maxlen=self.smooth)
        return track_id

    def _cleanup_tracks(self):
        stale_ids = [
            track_id for track_id, last_seen in self.track_last_seen.items()
            if self.frame_idx - last_seen > self.max_missing
        ]
        for track_id in stale_ids:
            self.track_buffers.pop(track_id, None)
            self.track_boxes.pop(track_id, None)
            self.track_last_seen.pop(track_id, None)
            self.track_last_probs.pop(track_id, None)
            self.track_last_result.pop(track_id, None)
            self.prob_hist.pop(track_id, None)
            self.fsm.pop(track_id)

        if len(self.track_last_seen) <= self.max_tracks:
            return
        keep_ids = sorted(
            self.track_last_seen.keys(),
            key=lambda item: self.track_last_seen[item],
            reverse=True,
        )[:self.max_tracks]
        keep_set = set(keep_ids)
        for track_id in list(self.track_last_seen.keys()):
            if track_id in keep_set:
                continue
            self.track_buffers.pop(track_id, None)
            self.track_boxes.pop(track_id, None)
            self.track_last_seen.pop(track_id, None)
            self.track_last_probs.pop(track_id, None)
            self.track_last_result.pop(track_id, None)
            self.prob_hist.pop(track_id, None)
            self.fsm.pop(track_id)

    def _sequence_entry(self, flat_points, frame_shape=None):
        kp = flat_points.reshape(17, 3).astype(np.float32)
        if frame_shape is not None and len(frame_shape) >= 2:
            frame_h, frame_w = int(frame_shape[0]), int(frame_shape[1])
        else:
            frame_w = int(max(np.max(kp[:, 0]), 640.0))
            frame_h = int(max(np.max(kp[:, 1]), 480.0))

        xy = kp[:, :2].copy()
        score = kp[:, 2].copy()
        low = score <= 0.0
        xy[:, 0] = np.clip(xy[:, 0] / max(frame_w, 1), 0.0, 1.0)
        xy[:, 1] = np.clip(xy[:, 1] / max(frame_h, 1), 0.0, 1.0)
        xy[low] = 0.0
        score[low] = 0.0
        return xy, score

    def _preprocess_sequence(self, seq):
        data = np.zeros((3, self.buffer_size, 17, 2), dtype=np.float32)
        seq_tail = seq[-self.buffer_size:]
        start = self.buffer_size - len(seq_tail)
        for idx, (xy, score) in enumerate(seq_tail):
            t_idx = start + idx
            data[0, t_idx, :, 0] = xy[:, 0]
            data[1, t_idx, :, 0] = xy[:, 1]
            data[2, t_idx, :, 0] = score

        invalid = data[2] == 0
        data[0][invalid] = 0
        data[1][invalid] = 0
        return torch.from_numpy(data).unsqueeze(0)

    def _compute_nearby_flags(self, active_track_ids):
        flags = {track_id: False for track_id in active_track_ids}
        ratio = self.fsm.cfg.fight_distance_ratio
        for idx, track_id in enumerate(active_track_ids):
            box_a = self.track_boxes[track_id]
            center_a = self._box_center(box_a)
            size_a = max(box_a[2] - box_a[0], box_a[3] - box_a[1], 1.0)
            for other_id in active_track_ids[idx + 1:]:
                box_b = self.track_boxes[other_id]
                center_b = self._box_center(box_b)
                size_b = max(box_b[2] - box_b[0], box_b[3] - box_b[1], 1.0)
                dist = float(np.linalg.norm(center_a - center_b))
                if dist <= ratio * max(size_a, size_b):
                    flags[track_id] = True
                    flags[other_id] = True
        return flags

    def _aggregate_existing_state(self):
        global_result = {"fall": False, "punch": False, "wave": False}
        self.last_overlays = []
        for track_id, one_result in self.track_last_result.items():
            if track_id not in self.track_boxes:
                continue
            global_result["fall"] = global_result["fall"] or bool(one_result.get("fall", False))
            global_result["wave"] = global_result["wave"] or bool(one_result.get("wave", False))
            global_result["punch"] = global_result["punch"] or bool(one_result.get("punch", False))
            self.last_overlays.append((self.track_boxes[track_id].copy(), {
                "fall": bool(one_result.get("fall", False)),
                "wave": bool(one_result.get("wave", False)),
                "punch": bool(
                    one_result.get("punch", False) or one_result.get("punch_candidate", False)
                ),
                "fall_prob": float(one_result.get("fall_prob", 0.0)),
                "wave_prob": float(one_result.get("wave_prob", 0.0)),
                "punch_prob": float(one_result.get("punch_prob", 0.0)),
            }))
        self.last_result = global_result
        return global_result

    def _avg_probs(self, track_id):
        hist = self.prob_hist.get(track_id)
        if hist:
            return np.mean(np.stack(list(hist), axis=0), axis=0)
        return self.track_last_probs.get(
            track_id, np.zeros((len(self.label_order),), dtype=np.float32)
        )

    def predict(self, points, bboxes, frame_shape=None):
        self.frame_idx += 1
        self.last_overlays = []

        if len(bboxes) == 0 or len(points) == 0:
            self._cleanup_tracks()
            return self._aggregate_existing_state()

        bboxes = np.asarray(bboxes, dtype=np.float32)
        points = np.asarray(points, dtype=np.float32)
        assigned_track_ids = self._assign_tracks(bboxes)

        for det_idx, box in enumerate(bboxes):
            track_id = assigned_track_ids[det_idx]
            if track_id == -1:
                if len(self.track_last_seen) >= self.max_tracks:
                    continue
                track_id = self._new_track(box)
                assigned_track_ids[det_idx] = track_id

            self.track_boxes[track_id] = box
            self.track_last_seen[track_id] = self.frame_idx
            self.track_buffers[track_id].append(
                self._sequence_entry(points[det_idx], frame_shape=frame_shape)
            )

        self._cleanup_tracks()

        active_track_ids = sorted(
            self.track_last_seen.keys(),
            key=lambda track_id: self._bbox_area(self.track_boxes[track_id]),
            reverse=True,
        )[:self.top_k_tracks]

        infer_track_ids = [
            track_id for track_id in active_track_ids
            if len(self.track_buffers.get(track_id, [])) >= self.min_frames
            and self.frame_idx % self.infer_interval == 0
        ]

        if infer_track_ids:
            batch = []
            for track_id in infer_track_ids:
                batch.append(self._preprocess_sequence(list(self.track_buffers[track_id])))
            x = torch.cat(batch, dim=0).float().to(self.device)

            with torch.no_grad():
                logits = self.model(x)
                probs = F.softmax(logits, dim=1).detach().cpu().numpy()

            for idx_in_batch, track_id in enumerate(infer_track_ids):
                self.track_last_probs[track_id] = probs[idx_in_batch]
                self.prob_hist[track_id].append(probs[idx_in_batch])

        nearby_flags = self._compute_nearby_flags(active_track_ids)
        global_result = {"fall": False, "punch": False, "wave": False}

        for track_id in active_track_ids:
            avg_prob = self._avg_probs(track_id)
            probs = {
                name: float(avg_prob[idx]) for name, idx in self.label_to_idx.items()
            }
            one_result = self.fsm.update(
                track_id,
                probs,
                has_nearby_person=nearby_flags.get(track_id, False),
            )
            self.track_last_result[track_id] = one_result

            global_result["fall"] = global_result["fall"] or bool(one_result.get("fall", False))
            global_result["wave"] = global_result["wave"] or bool(one_result.get("wave", False))
            global_result["punch"] = global_result["punch"] or bool(one_result.get("punch", False))

            overlay = {
                "fall": bool(one_result.get("fall", False)),
                "wave": bool(one_result.get("wave", False)),
                "punch": bool(
                    one_result.get("punch", False) or one_result.get("punch_candidate", False)
                ),
                "fall_prob": float(one_result.get("fall_prob", 0.0)),
                "wave_prob": float(one_result.get("wave_prob", 0.0)),
                "punch_prob": float(one_result.get("punch_prob", 0.0)),
            }
            self.last_overlays.append((self.track_boxes[track_id].copy(), overlay))

        self.last_result = global_result
        return self.last_result

    def get_last_overlays(self):
        return self.last_overlays
