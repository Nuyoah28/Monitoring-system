"""
Mamba-YOLO-World 推理封装类 (Open Vocabulary Object Detection)
================================================================
基于真正的 Mamba-YOLO-World 项目:
    https://github.com/Xuan-World/Mamba-YOLO-World
    (ICASSP 2025 Oral)

底层框架: mmyolo + mmdetection + mamba-ssm (状态空间模型)

设计目标: 与原来的 LoadEngineModel（TensorRT 烟火检测器）保持完全相同的调用接口:
    __call__(img_src: np.ndarray) -> (boxes, scores, idxs)

其中:
    - boxes  : np.ndarray [N, 4]  -> x1, y1, x2, y2
    - scores : np.ndarray [N]     -> 置信度得分
    - idxs   : np.ndarray [N]     -> 类别索引 (0=火, 1=烟, 2...=自定义)

这样 Yolov8_Pose.py 里的如下代码可以无缝兼容:
    fire_indices  = np.where(idxs1 == 0)[0]    # 火
    smoke_indices = np.where(idxs1 == 1)[0]    # 烟
"""

import sys
import os
import numpy as np
import torch

# ---------------------------------------------------------------
# 将 Mamba-YOLO-World 项目根目录加入 Python 搜索路径
# 这样才能正确 import yolo_world 模块和相关 mmyolo 依赖
# ---------------------------------------------------------------
MAMBA_YOLO_WORLD_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'Mamba-YOLO-World')
)
if MAMBA_YOLO_WORLD_ROOT not in sys.path:
    sys.path.insert(0, MAMBA_YOLO_WORLD_ROOT)


class MambaYOLODetector:
    """
    Mamba-YOLO-World 开放词汇目标检测封装器。
    
    基于 mmyolo/mmdetection 推理管线:
        1. Config.fromfile(config) -> 加载 Mamba2 配置
        2. init_detector(cfg, checkpoint) -> 初始化模型
        3. model.reparameterize(texts) -> 设置开放词汇检测类别
        4. model.test_step(data_batch) -> 单帧推理
        5. 解析 pred_instances -> bboxes, scores, labels

    内置固定类别 (与原 LoadEngineModel 兼容):
        index 0 = "fire"    (火)
        index 1 = "smoke"   (烟)
    
    可通过 extra_prompts 追加自定义检测目标 (index 从 2 开始)。
    """

    # 内置类别（固定顺序，与原下游代码 AlarmService.py 保持一致）
    BUILTIN_CATEGORIES = ["fire", "smoke"]

    def __init__(
        self,
        config_path: str,
        checkpoint_path: str,
        confidence: float = 0.3,
        max_dets: int = 100,
        extra_prompts: list = None,
        device: str = None,
    ):
        """
        参数:
            config_path (str): Mamba-YOLO-World 配置文件路径
                (如 'Mamba-YOLO-World/configs/mamba2_yolo_world_s.py')
            checkpoint_path (str): 模型权重文件路径 (.pth)
                (从 HuggingFace 或夸克网盘下载)
            confidence (float): 检测置信度阈值
            max_dets (int): 每帧最大检测数量
            extra_prompts (list): 除"火"和"烟"以外额外检测的目标，例如:
                ["bicycle in corridor", "person without helmet"]
            device (str): 推理设备，None 表示自动选择
        """
        self.confidence = confidence
        self.max_dets = max_dets
        self.device = device or ("cuda:0" if torch.cuda.is_available() else "cpu")

        # 完整类别列表，顺序决定 idxs 的值
        self.categories = self.BUILTIN_CATEGORIES.copy()
        if extra_prompts:
            self.categories.extend(extra_prompts)

        print(f"🚀 [Mamba-YOLO-World] 正在加载模型...")
        print(f"   配置文件: {config_path}")
        print(f"   权重文件: {checkpoint_path}")
        print(f"📋 [Mamba-YOLO-World] 检测类别({len(self.categories)}个): {self.categories}")

        # -------------------------------------------------------
        # 使用 mmdetection 标准 API 加载 Mamba-YOLO-World 模型
        # -------------------------------------------------------
        from mmengine.config import Config
        from mmengine.dataset import Compose
        from mmdet.apis import init_detector

        # 加载配置
        cfg = Config.fromfile(config_path)
        cfg.load_from = checkpoint_path

        # 初始化模型
        self.model = init_detector(cfg, checkpoint=checkpoint_path, device=self.device)

        # 构建测试数据管线
        # 关键: 将第一步改为 LoadImageFromNDArray，因为我们传入的是内存中的 numpy 数组
        self.model.cfg.test_dataloader.dataset.pipeline[0].type = 'mmdet.LoadImageFromNDArray'
        self.test_pipeline = Compose(self.model.cfg.test_dataloader.dataset.pipeline)

        # 设置开放词汇检测类别（Mamba-YOLO-World 核心能力）
        # 格式: texts = [["fire"], ["smoke"], ["bicycle"], [" "]]
        # 最后的 [" "] 是 YOLO-World 系列模型的惯例（用于兜底/背景类）
        self._update_texts()

        # 同步类别名称到画框工具，防止 draw_on_src() IndexError
        from Yolov8.utils1 import update_event_names
        update_event_names(self.categories)

        print(f"✅ [Mamba-YOLO-World] 模型加载成功！(设备: {self.device})")

    def _build_texts(self) -> list:
        """
        将类别列表转为 Mamba-YOLO-World 要求的格式:
            [["fire"], ["smoke"], ["bicycle"], [" "]]
        """
        return [[cat] for cat in self.categories] + [[' ']]

    def _update_texts(self):
        """使用 reparameterize 将文本类别嵌入到模型内部参数中。"""
        self.texts = self._build_texts()
        self.model.reparameterize(self.texts)

    def set_custom_prompts(self, prompts: list):
        """
        动态更新检测目标（无需重新加载模型）。
        前两个固定为 fire 和 smoke，传入的 prompts 追加其后。
        
        使用示例:
            detector.set_custom_prompts(["bicycle in corridor", "garbage on floor"])
        """
        self.categories = self.BUILTIN_CATEGORIES + prompts
        self._update_texts()
        # 同步类别名到画框工具
        from Yolov8.utils1 import update_event_names
        update_event_names(self.categories)
        print(f"🔄 [Mamba-YOLO-World] 已更新检测类别: {self.categories}")

    def __call__(self, img_src: np.ndarray):
        """
        对输入图像进行推理，返回与原 LoadEngineModel 完全相同格式的结果。

        参数:
            img_src (np.ndarray): BGR 格式的图像帧 (H, W, 3)

        返回:
            boxes  (np.ndarray): [N, 4] 边界框坐标 (x1, y1, x2, y2)
            scores (np.ndarray): [N] 置信度分数
            idxs   (np.ndarray): [N] 类别索引 (0=fire, 1=smoke, 2+=自定义)
        """
        # ---- 构建推理数据 ----
        # 注意: 视频帧推理时使用 img= (numpy array)
        # 图片文件推理时使用 img_path= (文件路径)
        data_info = dict(img_id=0, img=img_src, texts=self.texts)
        data_info = self.test_pipeline(data_info)
        data_batch = dict(
            inputs=data_info['inputs'].unsqueeze(0),
            data_samples=[data_info['data_samples']]
        )

        # ---- 执行推理 ----
        with torch.no_grad():
            output = self.model.test_step(data_batch)[0]
            pred_instances = output.pred_instances

            # 过滤低置信度检测
            pred_instances = pred_instances[
                pred_instances.scores.float() > self.confidence
            ]

        # 限制最大检测数量
        if len(pred_instances.scores) > self.max_dets:
            indices = pred_instances.scores.float().topk(self.max_dets)[1]
            pred_instances = pred_instances[indices]

        # ---- 转为 numpy 输出 ----
        pred_instances = pred_instances.cpu().numpy()

        if len(pred_instances['bboxes']) == 0:
            empty = np.empty((0,), dtype=np.float32)
            return np.empty((0, 4), dtype=np.float32), empty, empty

        boxes  = pred_instances['bboxes'].astype(np.float32)   # [N, 4]  x1y1x2y2
        scores = pred_instances['scores'].astype(np.float32)   # [N]
        idxs   = pred_instances['labels'].astype(np.int32)     # [N]  类别索引

        return boxes, scores, idxs
