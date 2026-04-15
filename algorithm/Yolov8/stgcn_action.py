"""
ST-GCN++ Action Recognition (matches PYSKL official weights exactly)
====================================================================
Pure PyTorch re-implementation of PYSKL's STGCN backbone + mstcn.
Architecture derived from reading PYSKL source code:
  - pyskl/models/gcns/stgcn.py
  - pyskl/models/gcns/utils/gcn.py  (unit_gcn)
  - pyskl/models/gcns/utils/tcn.py  (unit_tcn, mstcn)

Config that produced the weights:
  backbone: STGCN, gcn_adaptive='init', gcn_with_res=True,
            tcn_type='mstcn', graph layout='coco' mode='spatial'
  cls_head: GCNHead, num_classes=60, in_channels=256
  clip_len=100, num_person=2
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from collections import deque


# =====================================================================
# COCO-17 skeleton graph (layout='coco', mode='spatial')
# =====================================================================

COCO_PAIRS = [
    (0, 1), (0, 2), (1, 3), (2, 4),
    (0, 5), (0, 6),
    (5, 7), (7, 9),
    (6, 8), (8, 10),
    (5, 11), (6, 12),
    (11, 13), (13, 15),
    (12, 14), (14, 16),
    (5, 6), (11, 12),
]

NUM_JOINTS = 17


def build_spatial_adjacency(num_joints=17, edges=COCO_PAIRS, center=0):
    """Build 3-partition spatial adjacency matrix [3, V, V]."""
    # BFS distance from center
    dist = np.full(num_joints, np.inf)
    dist[center] = 0
    queue = [center]
    while queue:
        node = queue.pop(0)
        for i, j in edges:
            nbr = j if i == node else (i if j == node else None)
            if nbr is not None and dist[nbr] == np.inf:
                dist[nbr] = dist[node] + 1
                queue.append(nbr)

    A = np.zeros((3, num_joints, num_joints), dtype=np.float32)
    A[0] = np.eye(num_joints, dtype=np.float32)  # self-loops
    for i, j in edges:
        if dist[i] < dist[j]:
            A[1][j, i] = 1  # centripetal
            A[2][i, j] = 1  # centrifugal
        elif dist[i] > dist[j]:
            A[1][i, j] = 1
            A[2][j, i] = 1
        else:
            A[1][i, j] = 1
            A[1][j, i] = 1
    # Normalize
    for k in range(3):
        d = A[k].sum(axis=1, keepdims=True)
        d = np.maximum(d, 1e-6)
        A[k] /= d
    return A


# =====================================================================
# unit_tcn: Temporal Conv + BN (PYSKL: pyskl/models/gcns/utils/tcn.py)
# =====================================================================

class unit_tcn(nn.Module):
    """Single temporal conv block: Conv2d -> BN"""
    def __init__(self, in_channels, out_channels, kernel_size=9,
                 stride=1, dilation=1, norm=True):
        super().__init__()
        pad = (kernel_size + (kernel_size - 1) * (dilation - 1) - 1) // 2
        self.conv = nn.Conv2d(in_channels, out_channels, (kernel_size, 1),
                              (stride, 1), (pad, 0), (dilation, 1))
        self.bn = nn.BatchNorm2d(out_channels) if norm else nn.Identity()

    def forward(self, x):
        return self.bn(self.conv(x))


# =====================================================================
# mstcn: Multi-Scale Temporal Conv (PYSKL: pyskl/models/gcns/utils/tcn.py)
# ms_cfg = [(3,1), (3,2), (3,3), (3,4), ('max',3), '1x1']
# =====================================================================

class mstcn(nn.Module):
    def __init__(self, in_channels, out_channels, stride=1):
        super().__init__()
        ms_cfg = [(3, 1), (3, 2), (3, 3), (3, 4), ('max', 3), '1x1']
        num_branches = len(ms_cfg)
        mid_channels = out_channels // num_branches
        rem_mid_channels = out_channels - mid_channels * (num_branches - 1)

        branches = []
        for i, cfg in enumerate(ms_cfg):
            branch_c = rem_mid_channels if i == 0 else mid_channels
            if cfg == '1x1':
                branches.append(
                    nn.Conv2d(in_channels, branch_c, 1, stride=(stride, 1)))
            elif isinstance(cfg, tuple) and cfg[0] == 'max':
                branches.append(nn.Sequential(
                    nn.Conv2d(in_channels, branch_c, 1),
                    nn.BatchNorm2d(branch_c),
                    nn.ReLU(inplace=True),
                    nn.MaxPool2d((cfg[1], 1), (stride, 1), (1, 0))))
            else:
                ks, dil = cfg
                branches.append(nn.Sequential(
                    nn.Conv2d(in_channels, branch_c, 1),
                    nn.BatchNorm2d(branch_c),
                    nn.ReLU(inplace=True),
                    unit_tcn(branch_c, branch_c, kernel_size=ks,
                             stride=stride, dilation=dil, norm=False)))
            # Note: unit_tcn with norm=False means conv only, no BN inside

        self.branches = nn.ModuleList(branches)
        tin = mid_channels * (num_branches - 1) + rem_mid_channels
        self.transform = nn.Sequential(
            nn.BatchNorm2d(tin),
            nn.ReLU(inplace=True),
            nn.Conv2d(tin, out_channels, 1))
        self.bn = nn.BatchNorm2d(out_channels)

    def forward(self, x):
        branch_outs = [b(x) for b in self.branches]
        feat = torch.cat(branch_outs, dim=1)
        feat = self.transform(feat)
        return self.bn(feat)


# =====================================================================
# unit_gcn: Graph Conv (PYSKL: pyskl/models/gcns/utils/gcn.py)
# adaptive='init', conv_pos='pre', with_res=True
# =====================================================================

class unit_gcn(nn.Module):
    def __init__(self, in_channels, out_channels, A, adaptive='init',
                 with_res=True):
        super().__init__()
        self.num_subsets = A.shape[0]  # 3
        self.with_res = with_res

        # adaptive='init' -> A is nn.Parameter (learnable)
        if adaptive == 'init':
            self.A = nn.Parameter(torch.from_numpy(A).float())
        else:
            self.register_buffer('A', torch.from_numpy(A).float())

        # conv_pos='pre': conv then graph multiply
        self.conv = nn.Conv2d(in_channels, out_channels * self.num_subsets, 1)
        self.bn = nn.BatchNorm2d(out_channels)
        self.act = nn.ReLU(inplace=True)

        # Residual inside GCN (with_res=True)
        if with_res:
            if in_channels != out_channels:
                self.down = nn.Sequential(
                    nn.Conv2d(in_channels, out_channels, 1),
                    nn.BatchNorm2d(out_channels))
            else:
                self.down = None  # identity

    def forward(self, x, A=None):
        n, c, t, v = x.shape
        res = 0
        if self.with_res:
            res = self.down(x) if self.down is not None else x

        # A is learnable (adaptive='init')
        A = self.A

        # conv_pos='pre': conv first, then graph multiply
        x = self.conv(x)
        x = x.view(n, self.num_subsets, -1, t, v)
        x = torch.einsum('nkctv,kvw->nctw', x, A).contiguous()

        return self.act(self.bn(x) + res)


# =====================================================================
# STGCNBlock: GCN + TCN + Residual (PYSKL: pyskl/models/gcns/stgcn.py)
# =====================================================================

class STGCNBlock(nn.Module):
    def __init__(self, in_channels, out_channels, A, stride=1,
                 residual=True, **kwargs):
        super().__init__()
        self.gcn = unit_gcn(in_channels, out_channels, A,
                            adaptive='init', with_res=True)
        self.tcn = mstcn(out_channels, out_channels, stride=stride)
        self.relu = nn.ReLU(inplace=True)

        # Block-level residual (separate from GCN's internal residual)
        if not residual:
            self.residual = lambda x: 0
        elif in_channels == out_channels and stride == 1:
            self.residual = lambda x: x
        else:
            self.residual = unit_tcn(in_channels, out_channels,
                                     kernel_size=1, stride=stride)

    def forward(self, x, A=None):
        res = self.residual(x)
        x = self.tcn(self.gcn(x, A)) + res
        return self.relu(x)


# =====================================================================
# STGCN Backbone (PYSKL: pyskl/models/gcns/stgcn.py)
# =====================================================================

EPS = 1e-4

class STGCN(nn.Module):
    def __init__(self, in_channels=3, base_channels=64, num_classes=60,
                 ch_ratio=2, num_stages=10,
                 inflate_stages=[5, 8], down_stages=[5, 8]):
        super().__init__()

        A = build_spatial_adjacency()
        self.data_bn = nn.BatchNorm1d(in_channels * NUM_JOINTS)

        modules = []
        # Stage 1: in_channels -> base_channels (no residual)
        if in_channels != base_channels:
            modules.append(STGCNBlock(in_channels, base_channels, A,
                                      stride=1, residual=False))

        cur_channels = base_channels
        inflate_times = 0
        for i in range(2, num_stages + 1):
            stride = 1 + (i in down_stages)
            in_c = cur_channels
            if i in inflate_stages:
                inflate_times += 1
            out_c = int(base_channels * ch_ratio ** inflate_times + EPS)
            cur_channels = out_c
            modules.append(STGCNBlock(in_c, out_c, A, stride=stride))

        self.num_stages = num_stages if in_channels != base_channels else num_stages - 1
        self.gcn = nn.ModuleList(modules)

        # Classification head
        self.fc_cls = nn.Linear(256, num_classes)

    def forward(self, x):
        """x: (N, C, T, V, M)"""
        N, C, T, V, M = x.size()
        # Permute to N, M, V, C, T -> reshape for BN
        x = x.permute(0, 4, 3, 1, 2).contiguous()  # N, M, V, C, T
        x = x.view(N * M, V * C, T)
        x = self.data_bn(x)
        x = x.view(N * M, C, T, V)

        for i in range(self.num_stages):
            x = self.gcn[i](x)

        # x: (N*M, C, T', V)
        x = F.adaptive_avg_pool2d(x, 1)      # (N*M, 256, 1, 1)
        x = x.view(N, M, -1).mean(dim=1)     # (N, 256)
        x = self.fc_cls(x)
        return x


# =====================================================================
# NTU-RGB+D 60 Action Labels & Mapping
# =====================================================================

NTU60_LABELS = [
    "drink water", "eat meal", "brush teeth", "brush hair", "drop",
    "pick up", "throw", "sit down", "stand up", "clapping",
    "reading", "writing", "tear up paper", "put on jacket", "take off jacket",
    "put on a shoe", "take off a shoe", "put on glasses", "take off glasses",
    "put on a hat/cap",
    "take off a hat/cap", "cheer up", "hand waving", "kicking something",
    "reach into pocket",
    "hopping", "jump up", "phone call", "play with phone", "type on keyboard",
    "point to something", "taking a selfie", "check time (from watch)",
    "rub two hands", "nod head/bow",
    "shake head", "wipe face", "salute", "put palms together",
    "cross hands in front",
    "sneeze/cough", "staggering", "falling down", "headache/body pain",
    "chest pain",
    "back pain", "neck pain", "nausea/vomiting", "fan self",
    "punch/slap other person",
    "kicking other person", "pushing other person", "pat on back",
    "point finger at other",
    "hugging", "giving object", "touch pocket", "shaking hands",
    "walking towards",
    "walking apart",
]

# NTU-60 class index -> (system action, label) mapping
NTU_TO_ACTION = {
    42: ('fall', 'falling down'),
    41: ('fall', 'staggering'),
    49: ('punch', 'punch/slap'),
    50: ('punch', 'kicking other'),
    51: ('punch', 'pushing other'),
    22: ('wave', 'hand waving'),
}


# =====================================================================
# ActionRecognizer: High-level wrapper for the monitoring system
# =====================================================================

class ActionRecognizer:
    """
    Usage:
        ar = ActionRecognizer('algo/stgcnpp_ntu60.pth')
        result = ar.predict(points, bboxes)
        # result = {'fall': True, 'punch': False, 'wave': False}
    """

    def __init__(self, checkpoint_path, buffer_size=30,
                 confidence_threshold=0.5, device=None,
                 max_tracks=8, top_k_tracks=4, infer_interval=2,
                 max_missing=10):
        self.buffer_size = buffer_size
        self.confidence_threshold = confidence_threshold
        self.device = device or ('cuda:0' if torch.cuda.is_available() else 'cpu')
        self.max_tracks = max_tracks
        self.top_k_tracks = top_k_tracks
        self.infer_interval = infer_interval
        self.max_missing = max_missing
        self.frame_idx = 0
        self.next_track_id = 1
        self.track_buffers = {}      # track_id -> deque[(17,3)]
        self.track_boxes = {}        # track_id -> np.array([x1,y1,x2,y2])
        self.track_last_seen = {}    # track_id -> frame_idx
        self.track_last_result = {}  # track_id -> {'fall':bool,'punch':bool,'wave':bool}
        self.last_result = {'fall': False, 'punch': False, 'wave': False}
        self.last_overlays = []      # list[(bbox, action_dict)]
        self.num_classes = 60
        self.custom_label_names = []

        print(f"[ST-GCN++] Loading model...")
        print(f"   Weights: {checkpoint_path}")
        self.model = None

        try:
            ckpt = torch.load(checkpoint_path, map_location='cpu')
            ckpt_meta = {}
            if isinstance(ckpt, dict) and 'meta' in ckpt and isinstance(ckpt['meta'], dict):
                ckpt_meta = ckpt['meta']
            if isinstance(ckpt, dict) and 'state_dict' in ckpt:
                ckpt = ckpt['state_dict']
            # Remove 'backbone.' and 'cls_head.' prefixes from PYSKL keys
            cleaned = {}
            for k, v in ckpt.items():
                new_key = k.replace('backbone.', '').replace('cls_head.', '')
                cleaned[new_key] = v

            # Infer class count from checkpoint head shape.
            fc_weight = cleaned.get('fc_cls.weight')
            if fc_weight is not None and len(fc_weight.shape) == 2:
                self.num_classes = int(fc_weight.shape[0])
            else:
                self.num_classes = 60

            if self.num_classes != 60:
                default_names = ['normal', 'fall', 'punch', 'wave']
                label_names = ckpt_meta.get('label_names', default_names)
                if isinstance(label_names, (list, tuple)):
                    self.custom_label_names = [str(x).strip().lower() for x in label_names]
                else:
                    self.custom_label_names = default_names
                if len(self.custom_label_names) != self.num_classes:
                    self.custom_label_names = [f'class_{i}' for i in range(self.num_classes)]

            self.model = STGCN(in_channels=3, num_classes=self.num_classes)
            missing, unexpected = self.model.load_state_dict(cleaned, strict=False)
            print(f"   Weights loaded successfully!")
            if missing:
                print(f"   Missing keys: {missing[:5]}{' ...' if len(missing) > 5 else ''}")
            if unexpected:
                print(f"   Unexpected keys: {unexpected[:5]}{' ...' if len(unexpected) > 5 else ''}")
        except FileNotFoundError:
            print(f"   Weight file not found: {checkpoint_path}")
            print(f"   Using random weights (testing only)")
            self.num_classes = 60
            self.model = STGCN(in_channels=3, num_classes=self.num_classes)
        except Exception as e:
            print(f"   Weight loading error: {e}")
            print(f"   Using random weights (testing only)")
            self.num_classes = 60
            self.model = STGCN(in_channels=3, num_classes=self.num_classes)

        self.model.to(self.device)
        self.model.eval()
        print(f"   Device: {self.device}")
        print(f"   Buffer: {buffer_size} frames")
        print(f"   Threshold: {confidence_threshold}")
        print(f"   Multi-person: max_tracks={max_tracks}, top_k={top_k_tracks}, infer_interval={infer_interval}")

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

    def _assign_tracks(self, bboxes, iou_threshold=0.3):
        """Greedy IoU matching between current detections and existing tracks."""
        det_count = len(bboxes)
        assigned = [-1] * det_count
        if det_count == 0:
            return assigned

        track_ids = list(self.track_boxes.keys())
        if not track_ids:
            return assigned

        pairs = []
        for d_idx, box in enumerate(bboxes):
            for t_id in track_ids:
                iou = self._iou(box, self.track_boxes[t_id])
                if iou >= iou_threshold:
                    pairs.append((iou, d_idx, t_id))

        pairs.sort(reverse=True, key=lambda x: x[0])
        used_det = set()
        used_track = set()
        for _, d_idx, t_id in pairs:
            if d_idx in used_det or t_id in used_track:
                continue
            assigned[d_idx] = t_id
            used_det.add(d_idx)
            used_track.add(t_id)
        return assigned

    def _new_track(self, box):
        track_id = self.next_track_id
        self.next_track_id += 1
        self.track_buffers[track_id] = deque(maxlen=self.buffer_size)
        self.track_boxes[track_id] = box.astype(np.float32)
        self.track_last_seen[track_id] = self.frame_idx
        self.track_last_result[track_id] = {'fall': False, 'punch': False, 'wave': False}
        return track_id

    @staticmethod
    def _is_punch_like(label_name):
        name = label_name.lower()
        return (
            ('punch' in name) or ('fight' in name) or ('slap' in name) or
            ('kick' in name) or ('push' in name) or ('violent' in name)
        )

    @staticmethod
    def _is_wave_like(label_name):
        name = label_name.lower()
        return ('wave' in name) or ('help' in name)

    @staticmethod
    def _is_fall_like(label_name):
        name = label_name.lower()
        return ('fall' in name) or ('stagger' in name)

    @staticmethod
    def _normalize_pose(kp):
        """
        Person-centric normalization for better train/infer consistency.
        kp: (17,3) -> (x,y,conf)
        """
        kp = kp.astype(np.float32).copy()
        vis = kp[:, 2] > 0.05
        if np.sum(vis) < 2:
            return kp

        xy = kp[vis, :2]
        center = xy.mean(axis=0)
        span = xy.max(axis=0) - xy.min(axis=0)
        scale = float(max(span[0], span[1], 1e-3))
        kp[:, 0] = (kp[:, 0] - center[0]) / scale
        kp[:, 1] = (kp[:, 1] - center[1]) / scale
        return kp

    def _decode_probs(self, probs_vec):
        """Decode output probabilities into {'fall','punch','wave'} flags."""
        result = {'fall': False, 'punch': False, 'wave': False}
        if self.num_classes == 60:
            for ntu_idx, (action, _) in NTU_TO_ACTION.items():
                if probs_vec[ntu_idx].item() > self.confidence_threshold:
                    result[action] = True
            return result

        # Custom class mode: use argmax first (more stable than per-class thresholding).
        # Then gate with confidence_threshold.
        cls_idx = int(torch.argmax(probs_vec).item())
        cls_prob = float(probs_vec[cls_idx].item())
        if cls_prob < self.confidence_threshold:
            return result

        if 0 <= cls_idx < len(self.custom_label_names):
            label = self.custom_label_names[cls_idx]
        else:
            label = f"class_{cls_idx}"

        if self._is_fall_like(label):
            result['fall'] = True
        elif self._is_punch_like(label):
            result['punch'] = True
        elif self._is_wave_like(label):
            result['wave'] = True
        return result

    def _cleanup_tracks(self):
        stale_ids = [
            t_id for t_id, last_seen in self.track_last_seen.items()
            if self.frame_idx - last_seen > self.max_missing
        ]
        for t_id in stale_ids:
            self.track_buffers.pop(t_id, None)
            self.track_boxes.pop(t_id, None)
            self.track_last_seen.pop(t_id, None)
            self.track_last_result.pop(t_id, None)

        # keep track count bounded
        if len(self.track_last_seen) <= self.max_tracks:
            return
        keep_ids = sorted(
            self.track_last_seen.keys(),
            key=lambda t_id: self.track_last_seen[t_id],
            reverse=True
        )[:self.max_tracks]
        keep_set = set(keep_ids)
        for t_id in list(self.track_last_seen.keys()):
            if t_id not in keep_set:
                self.track_buffers.pop(t_id, None)
                self.track_boxes.pop(t_id, None)
                self.track_last_seen.pop(t_id, None)
                self.track_last_result.pop(t_id, None)

    def predict(self, points, bboxes):
        """Feed one frame and return aggregated multi-person action flags."""
        self.frame_idx += 1
        self.last_overlays = []

        if len(bboxes) == 0 or len(points) == 0:
            self._cleanup_tracks()
            return self.last_result

        bboxes = np.asarray(bboxes, dtype=np.float32)
        points = np.asarray(points, dtype=np.float32)
        assigned_track_ids = self._assign_tracks(bboxes)

        # Update tracks with current frame.
        for det_idx, box in enumerate(bboxes):
            track_id = assigned_track_ids[det_idx]
            if track_id == -1:
                if len(self.track_last_seen) >= self.max_tracks:
                    continue
                track_id = self._new_track(box)
                assigned_track_ids[det_idx] = track_id
            self.track_boxes[track_id] = box
            self.track_last_seen[track_id] = self.frame_idx
            kp = points[det_idx].reshape(17, 3)
            kp = self._normalize_pose(kp)
            self.track_buffers[track_id].append(kp)

        self._cleanup_tracks()

        # Select active tracks by area and run inference every N frames.
        active_track_ids = sorted(
            self.track_last_seen.keys(),
            key=lambda t_id: self._bbox_area(self.track_boxes[t_id]),
            reverse=True
        )[:self.top_k_tracks]

        infer_track_ids = [
            t_id for t_id in active_track_ids
            if len(self.track_buffers.get(t_id, [])) >= self.buffer_size
            and self.frame_idx % self.infer_interval == 0
        ]

        if infer_track_ids:
            batch = []
            for t_id in infer_track_ids:
                frames = np.array(list(self.track_buffers[t_id]), dtype=np.float32)  # (T,17,3)
                frames = frames.transpose(2, 0, 1)  # (3,T,17)
                batch.append(frames)
            x = torch.from_numpy(np.stack(batch, axis=0)).float().unsqueeze(-1).to(self.device)  # (N,3,T,17,1)

            with torch.no_grad():
                logits = self.model(x)
                probs = F.softmax(logits, dim=1)

            for idx_in_batch, t_id in enumerate(infer_track_ids):
                one_result = self._decode_probs(probs[idx_in_batch])
                self.track_last_result[t_id] = one_result

        # Aggregate track results as global result.
        global_result = {'fall': False, 'punch': False, 'wave': False}
        for t_id in active_track_ids:
            one_result = self.track_last_result.get(t_id, {})
            for action in global_result:
                global_result[action] = global_result[action] or bool(one_result.get(action, False))
            self.last_overlays.append((self.track_boxes[t_id].copy(), {
                'fall': bool(one_result.get('fall', False)),
                'punch': bool(one_result.get('punch', False)),
                'wave': bool(one_result.get('wave', False)),
            }))

        self.last_result = global_result
        return global_result

    def get_last_overlays(self):
        """Return per-track overlay info: [(bbox, {'fall':..,'punch':..,'wave':..}), ...]."""
        return self.last_overlays
