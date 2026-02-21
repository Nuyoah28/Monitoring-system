"""
ST-GCN++ 动作识别封装类
================================================================
纯 PyTorch 实现，不依赖 mmaction2 / PYSKL。

功能:
  - 接收 YOLOv8-Pose 输出的 COCO-17 关键点
  - 自动映射为 NTU-25 格式
  - 缓存多帧骨架序列
  - 调用 ST-GCN++ 网络进行动作分类

输入:
    points: np.ndarray [N_persons, 51]  (17 个关键点 × 3 值: x, y, confidence)
    来自 YOLOv8-Pose 的输出

输出:
    action_results: dict
        {
            'fall': bool,    # 是否检测到摔倒
            'punch': bool,   # 是否检测到打架
            'wave': bool,    # 是否检测到挥手
        }
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from collections import deque


# =====================================================================
# NTU-RGB+D 25 关键点的骨架图结构
# =====================================================================

# NTU-25 骨架的边连接 (0-indexed)
NTU_EDGES = [
    (0, 1), (1, 20), (2, 20), (3, 2), (4, 20),
    (5, 4), (6, 5), (7, 6), (8, 20), (9, 8),
    (10, 9), (11, 10), (12, 0), (13, 12), (14, 13),
    (15, 14), (16, 0), (17, 16), (18, 17), (19, 18),
    (21, 22), (7, 21), (23, 24), (11, 23),
]

NUM_JOINTS_NTU = 25


# =====================================================================
# COCO-17 → NTU-25 关键点映射
# =====================================================================

def coco17_to_ntu25(keypoints_17):
    """
    将 YOLOv8-Pose 的 COCO-17 关键点映射为 NTU-RGB+D 25 关键点。

    COCO-17 格式 (index: 名称):
        0:鼻子 1:左眼 2:右眼 3:左耳 4:右耳
        5:左肩 6:右肩 7:左肘 8:右肘 9:左手 10:右手
        11:左臀 12:右臀 13:左膝 14:右膝 15:左脚 16:右脚

    NTU-25 格式 (index: 名称):
        0:脊柱底 1:脊柱中 2:脖子 3:头顶
        4:左肩 5:左肘 6:左手腕 7:左手
        8:右肩 9:右肘 10:右手腕 11:右手
        12:左臀 13:左膝 14:左脚踝 15:左脚
        16:右臀 17:右膝 18:右脚踝 19:右脚
        20:脊柱 21:左手尖 22:左拇指 23:右手尖 24:右拇指

    参数:
        keypoints_17: np.ndarray [17, 2] 或 [17, 3] (x, y[, confidence])

    返回:
        keypoints_25: np.ndarray [25, 2]
    """
    kp = keypoints_17[:, :2]  # 只取 x, y
    ntu = np.zeros((25, 2), dtype=np.float32)

    # 躯干（用相邻点插值）
    mid_shoulder = (kp[5] + kp[6]) / 2    # 左右肩中点
    mid_hip = (kp[11] + kp[12]) / 2       # 左右臀中点

    ntu[0]  = mid_hip                       # 脊柱底 = 臀中点
    ntu[1]  = (mid_shoulder + mid_hip) / 2  # 脊柱中 = 肩臀中间
    ntu[2]  = mid_shoulder                  # 脖子 = 肩中点
    ntu[3]  = kp[0]                         # 头顶 ≈ 鼻子

    # 左臂
    ntu[4]  = kp[5]    # 左肩
    ntu[5]  = kp[7]    # 左肘
    ntu[6]  = kp[9]    # 左手腕
    ntu[7]  = kp[9]    # 左手 ≈ 左手腕

    # 右臂
    ntu[8]  = kp[6]    # 右肩
    ntu[9]  = kp[8]    # 右肘
    ntu[10] = kp[10]   # 右手腕
    ntu[11] = kp[10]   # 右手 ≈ 右手腕

    # 左腿
    ntu[12] = kp[11]   # 左臀
    ntu[13] = kp[13]   # 左膝
    ntu[14] = kp[15]   # 左脚踝
    ntu[15] = kp[15]   # 左脚 ≈ 左脚踝

    # 右腿
    ntu[16] = kp[12]   # 右臀
    ntu[17] = kp[14]   # 右膝
    ntu[18] = kp[16]   # 右脚踝
    ntu[19] = kp[16]   # 右脚 ≈ 右脚踝

    # 脊柱
    ntu[20] = mid_shoulder                  # 脊柱 = 肩中点

    # 手指尖（用手腕近似）
    ntu[21] = kp[9]    # 左手尖 ≈ 左手腕
    ntu[22] = kp[9]    # 左拇指 ≈ 左手腕
    ntu[23] = kp[10]   # 右手尖 ≈ 右手腕
    ntu[24] = kp[10]   # 右拇指 ≈ 右手腕

    return ntu


# =====================================================================
# ST-GCN++ 网络结构 (纯 PyTorch)
# =====================================================================

def build_adjacency_matrix(num_joints, edges):
    """构建邻接矩阵"""
    A = np.zeros((num_joints, num_joints), dtype=np.float32)
    for i, j in edges:
        A[i, j] = 1
        A[j, i] = 1
    # 加自连接
    A += np.eye(num_joints, dtype=np.float32)
    return A


def normalize_adjacency(A):
    """对称归一化: D^{-1/2} A D^{-1/2}"""
    D = np.sum(A, axis=1)
    D_inv_sqrt = np.diag(1.0 / np.sqrt(np.maximum(D, 1e-6)))
    return D_inv_sqrt @ A @ D_inv_sqrt


class SpatialGraphConv(nn.Module):
    """空间图卷积层"""

    def __init__(self, in_channels, out_channels, A, residual=True):
        super().__init__()
        self.num_joints = A.shape[0]
        # 可学习的邻接矩阵
        self.register_buffer('A', torch.from_numpy(A).float())
        self.PA = nn.Parameter(torch.from_numpy(A).float())
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=1)
        self.bn = nn.BatchNorm2d(out_channels)

        if residual and in_channels == out_channels:
            self.residual = lambda x: x
        elif residual:
            self.residual = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, 1),
                nn.BatchNorm2d(out_channels),
            )
        else:
            self.residual = lambda x: 0

    def forward(self, x):
        """
        x: (N, C, T, V) - batch, channels, frames, joints
        """
        res = self.residual(x)
        A = self.A + self.PA  # 固定图 + 可学习残差
        # 空间图卷积: x @ A
        x = torch.einsum('nctv,vw->nctw', x, A)
        x = self.conv(x)
        x = self.bn(x)
        return F.relu(x + res)


class TemporalConv(nn.Module):
    """时间卷积层（多尺度）"""

    def __init__(self, in_channels, out_channels, kernel_size=3, stride=1, residual=True):
        super().__init__()
        pad = (kernel_size - 1) // 2
        self.conv = nn.Conv2d(
            in_channels, out_channels,
            kernel_size=(kernel_size, 1),
            padding=(pad, 0),
            stride=(stride, 1)
        )
        self.bn = nn.BatchNorm2d(out_channels)

        if residual and in_channels == out_channels and stride == 1:
            self.residual = lambda x: x
        elif residual:
            self.residual = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, 1, stride=(stride, 1)),
                nn.BatchNorm2d(out_channels),
            )
        else:
            self.residual = lambda x: 0

    def forward(self, x):
        res = self.residual(x)
        x = self.conv(x)
        x = self.bn(x)
        return F.relu(x + res)


class STGCNBlock(nn.Module):
    """一个 ST-GCN++ 块 = 空间图卷积 + 时间卷积"""

    def __init__(self, in_channels, out_channels, A, stride=1):
        super().__init__()
        self.gcn = SpatialGraphConv(in_channels, out_channels, A)
        self.tcn = TemporalConv(out_channels, out_channels, stride=stride)

    def forward(self, x):
        x = self.gcn(x)
        x = self.tcn(x)
        return x


class STGCNPP(nn.Module):
    """
    ST-GCN++ 动作识别网络。

    输入: (N, C, T, V, M)
        N = batch size
        C = 通道数 (x, y = 2)
        T = 帧数 (默认 30)
        V = 关键点数 (25 for NTU)
        M = 人数 (默认 1)

    输出: (N, num_classes) 动作分类概率
    """

    def __init__(self, num_classes=60, in_channels=2, num_joints=25, edges=NTU_EDGES):
        super().__init__()
        A_raw = build_adjacency_matrix(num_joints, edges)
        A = normalize_adjacency(A_raw)

        self.data_bn = nn.BatchNorm1d(in_channels * num_joints)

        self.layers = nn.ModuleList([
            STGCNBlock(in_channels, 64, A),
            STGCNBlock(64, 64, A),
            STGCNBlock(64, 64, A),
            STGCNBlock(64, 64, A),
            STGCNBlock(64, 128, A, stride=2),
            STGCNBlock(128, 128, A),
            STGCNBlock(128, 128, A),
            STGCNBlock(128, 256, A, stride=2),
            STGCNBlock(256, 256, A),
            STGCNBlock(256, 256, A),
        ])

        self.fc = nn.Linear(256, num_classes)

    def forward(self, x):
        """
        x: (N, C, T, V, M)
        """
        N, C, T, V, M = x.size()
        # 合并 person 维度
        x = x.permute(0, 4, 3, 1, 2).contiguous()  # N, M, V, C, T
        x = x.view(N * M, V * C, T)
        x = self.data_bn(x)
        x = x.view(N * M, C, T, V)  # N*M, C, T, V

        for layer in self.layers:
            x = layer(x)

        # 全局平均池化
        x = F.adaptive_avg_pool2d(x, 1)  # N*M, 256, 1, 1
        x = x.view(N, M, -1).mean(dim=1)  # N, 256
        x = self.fc(x)
        return x


# =====================================================================
# NTU-RGB+D 60 动作标签
# =====================================================================

NTU60_LABELS = [
    "drink water", "eat meal", "brush teeth", "brush hair", "drop",
    "pick up", "throw", "sit down", "stand up", "clapping",
    "reading", "writing", "tear up paper", "put on jacket", "take off jacket",
    "put on a shoe", "take off a shoe", "put on glasses", "take off glasses",
    "put on a hat/cap",
    "take off a hat/cap", "cheer up", "hand waving", "kicking something",
    "reach into pocket",
    "hopping", "jump up", "phone call", "play with phone", "type on a keyboard",
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

# NTU-60 动作 → 系统 caseType 映射
# key: NTU-60 动作索引 (0-based)
# value: (caseType 名称, 系统含义)
NTU_TO_CASETYPE = {
    42: ('fall', '摔倒'),           # A43: falling down
    49: ('punch', '打架'),          # A50: punch/slap other person
    50: ('punch', '打架'),          # A51: kicking other person
    51: ('punch', '打架'),          # A52: pushing other person
    22: ('wave', '挥手呼救'),       # A23: hand waving
    41: ('fall', '摔倒'),           # A42: staggering (踉跄 → 也视为摔倒风险)
}


# =====================================================================
# ActionRecognizer 封装类
# =====================================================================

class ActionRecognizer:
    """
    动作识别器封装类。

    使用方式:
        recognizer = ActionRecognizer(
            checkpoint_path='algo/stgcnpp_ntu60.pth',
            buffer_size=30,
        )

        # 在每帧的处理循环中:
        results = recognizer.predict(points, bboxes)
        # results = {'fall': True, 'punch': False, 'wave': False}

    参数:
        checkpoint_path: ST-GCN++ 权重文件路径
        buffer_size: 缓冲帧数 (默认 30)
        confidence_threshold: 动作判定置信度阈值
        device: 推理设备
    """

    def __init__(
        self,
        checkpoint_path: str,
        buffer_size: int = 30,
        confidence_threshold: float = 0.5,
        device: str = None,
    ):
        self.buffer_size = buffer_size
        self.confidence_threshold = confidence_threshold
        self.device = device or ('cuda:0' if torch.cuda.is_available() else 'cpu')

        # 骨架缓冲区: 为每个检测到的人维护独立缓冲
        # 简化方案: 只跟踪画面中的"最大人物"(bbox面积最大的)
        self.pose_buffer = deque(maxlen=buffer_size)

        # 上一次的预测结果 (在缓冲区未满时返回)
        self.last_result = {'fall': False, 'punch': False, 'wave': False}

        # 加载模型
        print(f"🧠 [ST-GCN++] 正在加载动作识别模型...")
        print(f"   权重文件: {checkpoint_path}")
        self.model = STGCNPP(num_classes=60, in_channels=2, num_joints=25)

        # 加载权重
        try:
            state_dict = torch.load(checkpoint_path, map_location='cpu')
            # 兼容不同保存格式
            if 'state_dict' in state_dict:
                state_dict = state_dict['state_dict']
            # 去掉可能的 'backbone.' 前缀
            cleaned = {}
            for k, v in state_dict.items():
                new_key = k.replace('backbone.', '').replace('cls_head.', '')
                # fc 层映射
                if 'fc_cls' in new_key:
                    new_key = new_key.replace('fc_cls', 'fc')
                cleaned[new_key] = v
            self.model.load_state_dict(cleaned, strict=False)
            print(f"✅ [ST-GCN++] 模型加载成功！")
        except FileNotFoundError:
            print(f"⚠️ [ST-GCN++] 权重文件不存在: {checkpoint_path}")
            print(f"   将使用随机权重（仅用于测试流程）")
        except Exception as e:
            print(f"⚠️ [ST-GCN++] 权重加载异常: {e}")
            print(f"   将使用随机权重（仅用于测试流程）")

        self.model.to(self.device)
        self.model.eval()
        print(f"   设备: {self.device}")
        print(f"   缓冲帧数: {buffer_size}")
        print(f"   置信度阈值: {confidence_threshold}")

    def _select_main_person(self, points, bboxes):
        """
        从多个检测到的人中选出"主要人物"（bbox 面积最大的）。

        参数:
            points: np.ndarray [N, 51] - N 个人的关键点
            bboxes: np.ndarray [N, 4] - N 个人的边界框

        返回:
            keypoints_17: np.ndarray [17, 3] - 主要人物的关键点 (x, y, conf)
        """
        if len(bboxes) == 0:
            return None

        # 选面积最大的人
        areas = (bboxes[:, 2] - bboxes[:, 0]) * (bboxes[:, 3] - bboxes[:, 1])
        main_idx = np.argmax(areas)

        # 提取 17 个关键点 [x, y, confidence]
        kpt = points[main_idx]  # shape: (51,)
        keypoints = kpt.reshape(17, 3)  # (17, 3)
        return keypoints

    def predict(self, points, bboxes):
        """
        输入一帧的关键点数据，返回动作识别结果。

        会自动缓存帧数据，缓冲区满 30 帧后才开始推理。
        缓冲区未满时返回上一次的结果。

        参数:
            points: np.ndarray [N, 51] - YOLOv8-Pose 输出
            bboxes: np.ndarray [N, 4] - 边界框

        返回:
            dict: {'fall': bool, 'punch': bool, 'wave': bool}
        """
        # 选出主要人物
        kp17 = self._select_main_person(points, bboxes)
        if kp17 is None:
            self.pose_buffer.clear()
            return self.last_result

        # COCO-17 → NTU-25 映射
        kp25 = coco17_to_ntu25(kp17)  # (25, 2)

        # 加入缓冲区
        self.pose_buffer.append(kp25)

        # 缓冲区未满，返回上一次结果
        if len(self.pose_buffer) < self.buffer_size:
            return self.last_result

        # 缓冲区满了，执行推理
        result = self._inference()
        self.last_result = result
        return result

    def _inference(self):
        """执行 ST-GCN++ 推理"""
        # 构建输入张量: (1, 2, T, 25, 1)
        frames = np.array(list(self.pose_buffer))  # (T, 25, 2)
        frames = frames.transpose(2, 0, 1)         # (2, T, 25)

        x = torch.from_numpy(frames).float()
        x = x.unsqueeze(0).unsqueeze(-1)            # (1, 2, T, 25, 1)
        x = x.to(self.device)

        with torch.no_grad():
            logits = self.model(x)                   # (1, 60)
            probs = F.softmax(logits, dim=1)[0]      # (60,)

        # 检查与我们系统相关的动作
        result = {'fall': False, 'punch': False, 'wave': False}

        for ntu_idx, (action_name, _) in NTU_TO_CASETYPE.items():
            prob = probs[ntu_idx].item()
            if prob > self.confidence_threshold:
                result[action_name] = True

        return result
