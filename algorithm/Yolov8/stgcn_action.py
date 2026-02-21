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
                 confidence_threshold=0.5, device=None):
        self.buffer_size = buffer_size
        self.confidence_threshold = confidence_threshold
        self.device = device or ('cuda:0' if torch.cuda.is_available() else 'cpu')
        self.pose_buffer = deque(maxlen=buffer_size)
        self.last_result = {'fall': False, 'punch': False, 'wave': False}

        print(f"[ST-GCN++] Loading model...")
        print(f"   Weights: {checkpoint_path}")
        self.model = STGCN(in_channels=3, num_classes=60)

        try:
            ckpt = torch.load(checkpoint_path, map_location='cpu')
            if 'state_dict' in ckpt:
                ckpt = ckpt['state_dict']
            # Remove 'backbone.' and 'cls_head.' prefixes from PYSKL keys
            cleaned = {}
            for k, v in ckpt.items():
                new_key = k.replace('backbone.', '').replace('cls_head.', '')
                cleaned[new_key] = v
            self.model.load_state_dict(cleaned, strict=True)
            print(f"   Weights loaded successfully!")
        except FileNotFoundError:
            print(f"   Weight file not found: {checkpoint_path}")
            print(f"   Using random weights (testing only)")
        except Exception as e:
            print(f"   Weight loading error: {e}")
            print(f"   Using random weights (testing only)")

        self.model.to(self.device)
        self.model.eval()
        print(f"   Device: {self.device}")
        print(f"   Buffer: {buffer_size} frames")
        print(f"   Threshold: {confidence_threshold}")

    def _select_main_person(self, points, bboxes):
        """Select person with largest bounding box."""
        if len(bboxes) == 0:
            return None
        areas = (bboxes[:, 2] - bboxes[:, 0]) * (bboxes[:, 3] - bboxes[:, 1])
        idx = np.argmax(areas)
        return points[idx].reshape(17, 3)  # (17, 3) = x, y, conf

    def predict(self, points, bboxes):
        """Feed one frame, get action detection results."""
        kp = self._select_main_person(points, bboxes)
        if kp is None:
            self.pose_buffer.clear()
            return self.last_result

        self.pose_buffer.append(kp)
        if len(self.pose_buffer) < self.buffer_size:
            return self.last_result

        result = self._inference()
        self.last_result = result
        return result

    def _inference(self):
        """Run ST-GCN++ on buffered frames."""
        frames = np.array(list(self.pose_buffer))  # (T, 17, 3)
        frames = frames.transpose(2, 0, 1)         # (3, T, 17)

        x = torch.from_numpy(frames).float()
        x = x.unsqueeze(0).unsqueeze(-1)            # (1, 3, T, 17, 1) = N,C,T,V,M
        x = x.to(self.device)

        with torch.no_grad():
            logits = self.model(x)
            probs = F.softmax(logits, dim=1)[0]

        result = {'fall': False, 'punch': False, 'wave': False}
        for ntu_idx, (action, _) in NTU_TO_ACTION.items():
            if probs[ntu_idx].item() > self.confidence_threshold:
                result[action] = True
        return result
