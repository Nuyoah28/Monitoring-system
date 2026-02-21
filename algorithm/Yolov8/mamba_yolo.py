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
        # 需要在导入torch后再确定设备
        import torch
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
        # 使用替代方法加载 Mamba-YOLO-World 模型
        # -------------------------------------------------------
        # 为了避免与transformers库的循环导入问题，延后导入
        import warnings
        warnings.filterwarnings("ignore", category=FutureWarning)
        from mmengine.config import Config
        from mmengine.dataset import Compose
        import torch
        import tempfile
        import os as os_temp
        
        # 自定义兼容性 IoULoss 类以处理 iou_mode 参数
        from mmdet.models.losses.iou_loss import IoULoss as OriginalIoULoss
        from mmdet.registry import MODELS as MMDET_MODELS
        import inspect
        
        class CompatibleIoULoss(OriginalIoULoss):
            """兼容性 IoULoss 类，处理旧版配置中可能存在的不兼容参数"""
            def __init__(self, *args, **kwargs):
                # 移除会导致问题的参数
                # 注意：'return_iou' 在某些版本的 IoULoss 中可能不被接受
                kwargs.pop('iou_mode', None)  # 移除 iou_mode 参数
                kwargs.pop('bbox_format', None)  # 移除 bbox_format 参数
                kwargs.pop('return_iou', None)  # 移除 return_iou 参数（根据错误信息，这也是问题参数）
                # 保留原始IoULoss构造函数需要的参数：eps, reduction, loss_weight 等
                super().__init__(*args, **kwargs)
        
        # 重要：需要导入Mamba-YOLO-World的自定义模块
        # 这会将YOLOWorldDetector等组件注册到模型注册表中
        import sys
        
        MAMBA_YOLO_WORLD_ROOT = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', 'Mamba-YOLO-World')
        )
        if MAMBA_YOLO_WORLD_ROOT not in sys.path:
            sys.path.insert(0, MAMBA_YOLO_WORLD_ROOT)
        
        # 确保注册了必要的组件 - 在加载配置前导入模块
        try:
            # 导入必要的模块以确保它们被注册
            from mmdet.utils import register_all_modules
            register_all_modules()
            
            # 重要：在加载配置前先导入并注册yolo-world模块
            # 确保所有必要组件被注册到mmdet模型注册表中
            import yolo_world
            from mmdet.registry import MODELS as MMDET_MODELS
            
            # 导入yolo-world需要的组件
            from yolo_world.models.detectors.yolo_world import YOLOWorldDetector
            from yolo_world.models.data_preprocessors.data_preprocessor import YOLOWDetDataPreprocessor
            from yolo_world.models.backbones.mm_backbone import MultiModalYOLOBackbone
            from yolo_world.models.necks.mamba_yolo_world_pafpn import MambaYOLOWorldPAFPN
            from yolo_world.models.dense_heads.yolo_world_head import YOLOWorldHead, YOLOWorldHeadModule
            from yolo_world.models.backbones.mm_backbone import HuggingCLIPLanguageBackbone  # 文本编码器
            from yolo_world.models.layers.mamba2_yolo_bricks import MambaFusionCSPLayerWithTwoConv2, TextGuidedODSSBlock2, TextGuidedSS2D2  # Mamba特殊层
            from yolo_world.models.layers.mamba2_simple import Mamba2Simple  # Mamba2简化版本
            
            # 导入基础的mmyolo组件（根据Mamba-YOLO-World配置文件的依赖）
            from mmyolo.models.backbones.csp_darknet import YOLOv8CSPDarknet
            from mmyolo.models.layers.yolo_bricks import SPPFBottleneck, CSPResLayer
            from mmyolo.models.data_preprocessors import YOLOv5DetDataPreprocessor
            
            # 导入并注册损失函数组件
            from mmdet.models.losses.iou_loss import IoULoss, BoundedIoULoss, GIoULoss, DIoULoss, CIoULoss
            from mmyolo.models.losses import IoULoss as YOLOv5IoULoss
            
            # 导入并注册任务分配器组件
            from mmyolo.models.task_modules.assigners.batch_task_aligned_assigner import BatchTaskAlignedAssigner
            from mmyolo.registry import TASK_UTILS as MYOLO_TASK_UTILS
            from mmdet.registry import TASK_UTILS as MMDET_TASK_UTILS
            
            # 导入并注册转换器组件
            from mmyolo.datasets.transforms.transforms import LetterResize
            from mmengine.registry import TRANSFORMS as MMENGINE_TRANSFORMS
            from mmdet.registry import TRANSFORMS as MMDET_TRANSFORMS
            from mmyolo.registry import TRANSFORMS as MYOLO_TRANSFORMS
            
            # 导入常见的 MMDetection 转换器组件
            # 使用更确定的导入方式
            try:
                # 直接尝试导入 MMDetection 中最常用的 Normalize 组件
                from mmdet.datasets.transforms import Normalize
            except ImportError:
                try:
                    # 尝试从 MMYOLO 中获取（可能已预配置）
                    from mmyolo.datasets.transforms import Normalize
                except ImportError:
                    # 创建一个兼容性的 Normalize 类
                    import numpy as np
                    from mmcv.image import imnormalize
                    from mmengine.registry import TRANSFORMS as MMCV_TRANSFORMS
                    from typing import Sequence
                    
                    class Normalize:
                        """MMDetection风格的Normalize变换，用于图像标准化"""
                        
                        def __init__(self, mean: Sequence[float], std: Sequence[float], to_rgb: bool = True):
                            self.mean = np.array(mean, dtype=np.float32)
                            self.std = np.array(std, dtype=np.float32)
                            self.to_rgb = to_rgb
                        
                        def __call__(self, results: dict) -> dict:
                            """应用标准化变换"""
                            img = results['img']
                            results['img'] = imnormalize(img, self.mean, self.std, self.to_rgb)
                            results['img_norm_cfg'] = dict(mean=self.mean, std=self.std, to_rgb=self.to_rgb)
                            return results
                        
                        def __repr__(self):
                            repr_str = self.__class__.__name__
                            repr_str += f'(mean={list(self.mean)}, '
                            repr_str += f'std={list(self.std)}, '
                            repr_str += f'to_rgb={self.to_rgb})'
                            return repr_str
                    
                    # 尝试注册到 MMCV 的 TRANSFORMS（如果可用）
                    try:
                        MMCV_TRANSFORMS.register_module(name='Normalize', module=Normalize)
                    except:
                        pass  # 如果注册失败，继续使用
            
            try:
                # 直接尝试导入 MMDetection 中最常用的 PackDetInputs 组件
                from mmdet.datasets.transforms import PackDetInputs
            except ImportError:
                try:
                    # 尝试从 MMYOLO 中获取
                    from mmyolo.datasets.transforms import PackDetInputs
                except ImportError:
                    # 从 MMDetection 的 formatting 模块导入
                    try:
                        from mmdet.datasets.transforms.formatting import PackDetInputs
                    except ImportError:
                        # 定义一个简化版本
                        class PackDetInputs:
                            """MMDetection风格的PackDetInputs变换，用于打包检测输入"""
                            
                            def __init__(self, meta_keys=('img_id', 'img_path', 'ori_shape', 'img_shape', 'scale_factor')):
                                self.meta_keys = meta_keys
                            
                            def __call__(self, results: dict) -> dict:
                                """打包检测输入数据"""
                                packed_results = dict()
                                
                                # 添加图像数据
                                if 'img' in results:
                                    packed_results['inputs'] = results['img'].transpose(2, 0, 1)
                                
                                # 添加元数据
                                meta = dict()
                                for key in self.meta_keys:
                                    if key in results:
                                        meta[key] = results[key]
                                
                                # 如果有标注数据，也添加
                                if 'gt_bboxes' in results:
                                    meta['gt_bboxes'] = results['gt_bboxes']
                                if 'gt_labels' in results:
                                    meta['gt_labels'] = results['gt_labels']
                                
                                packed_results['data_samples'] = meta
                                return packed_results
                            
                            def __repr__(self):
                                repr_str = self.__class__.__name__
                                repr_str += f'(meta_keys={self.meta_keys})'
                                return repr_str
            
            # 导入并注册任务分配器组件
            from mmyolo.models.task_modules.assigners.batch_task_aligned_assigner import BatchTaskAlignedAssigner
            
            # 显式注册到mmdet模型注册表
            components_to_register = [
                ('YOLOWorldDetector', YOLOWorldDetector),
                ('YOLOWDetDataPreprocessor', YOLOWDetDataPreprocessor),
                ('MultiModalYOLOBackbone', MultiModalYOLOBackbone),
                ('MambaYOLOWorldPAFPN', MambaYOLOWorldPAFPN),
                ('YOLOWorldHead', YOLOWorldHead),
                ('YOLOWorldHeadModule', YOLOWorldHeadModule),
                # 文本编码器
                ('HuggingCLIPLanguageBackbone', HuggingCLIPLanguageBackbone),
                # Mamba特殊层
                ('MambaFusionCSPLayerWithTwoConv2', MambaFusionCSPLayerWithTwoConv2),
                ('TextGuidedODSSBlock2', TextGuidedODSSBlock2),
                ('TextGuidedSS2D2', TextGuidedSS2D2),
                ('Mamba2Simple', Mamba2Simple),
                # mmyolo组件
                ('YOLOv8CSPDarknet', YOLOv8CSPDarknet),
                ('SPPFBottleneck', SPPFBottleneck),
                ('CSPResLayer', CSPResLayer),
                ('YOLOv5DetDataPreprocessor', YOLOv5DetDataPreprocessor),
                # 损失函数组件
                ('IoULoss', IoULoss),
                ('BoundedIoULoss', BoundedIoULoss),
                ('GIoULoss', GIoULoss),
                ('DIoULoss', DIoULoss),
                ('CIoULoss', CIoULoss),
                ('YOLOv5IoULoss', YOLOv5IoULoss),
                # 兼容性损失函数
                ('CompatibleIoULoss', CompatibleIoULoss)
            ]
            
            for name, module in components_to_register:
                if name not in MMDET_MODELS.module_dict:
                    MMDET_MODELS.register_module(name=name, module=module)
            
            # 特殊处理：BatchTaskAlignedAssigner 需要注册到多个 TASK_UTILS 注册表
            if 'BatchTaskAlignedAssigner' not in MYOLO_TASK_UTILS.module_dict:
                MYOLO_TASK_UTILS.register_module(name='BatchTaskAlignedAssigner', module=BatchTaskAlignedAssigner)
            if 'BatchTaskAlignedAssigner' not in MMDET_TASK_UTILS.module_dict:
                MMDET_TASK_UTILS.register_module(name='BatchTaskAlignedAssigner', module=BatchTaskAlignedAssigner)
            
            # 特殊处理：LetterResize 需要注册到多个 TRANSFORMS 注册表
            if 'LetterResize' not in MYOLO_TRANSFORMS.module_dict:
                MYOLO_TRANSFORMS.register_module(name='LetterResize', module=LetterResize)
            if 'LetterResize' not in MMDET_TRANSFORMS.module_dict:
                MMDET_TRANSFORMS.register_module(name='LetterResize', module=LetterResize)
            
            # 特殊处理：Normalize 需要注册到 TRANSFORMS 注册表（如果组件有效）
            if Normalize is not None and hasattr(Normalize, '__name__'):
                if 'Normalize' not in MMDET_TRANSFORMS.module_dict:
                    MMDET_TRANSFORMS.register_module(name='Normalize', module=Normalize)
            
            # 特殊处理：确保 Normalize 注册到 MMDetection TRANSFORMS 注册表
            # 检查是否已存在，如果不存在则注册
            if 'Normalize' not in MMDET_TRANSFORMS.module_dict:
                try:
                    MMDET_TRANSFORMS.register_module(name='Normalize', module=Normalize)
                except Exception:
                    # 如果注册失败，尝试重新注册（可能已有实例）
                    pass
            
            # 特殊处理：确保 PackDetInputs 注册到 MMDetection TRANSFORMS 注册表
            # 检查是否已存在，如果不存在则注册
            if 'PackDetInputs' not in MMDET_TRANSFORMS.module_dict:
                try:
                    MMDET_TRANSFORMS.register_module(name='PackDetInputs', module=PackDetInputs)
                except Exception:
                    # 如果注册失败，尝试重新注册（可能已有实例）
                    pass
            
            # 特殊处理：确保 Normalize 注册到 MMDetection TRANSFORMS 注册表
            # 检查是否已存在，如果不存在则注册
            if 'Normalize' not in MMDET_TRANSFORMS.module_dict:
                try:
                    MMDET_TRANSFORMS.register_module(name='Normalize', module=Normalize)
                except Exception:
                    # 如果注册失败，尝试重新注册（可能已有实例）
                    pass
            
            # 特殊处理：确保 PackDetInputs 注册到 MMDetection TRANSFORMS 注册表
            # 检查是否已存在，如果不存在则注册
            if 'PackDetInputs' not in MMDET_TRANSFORMS.module_dict:
                try:
                    MMDET_TRANSFORMS.register_module(name='PackDetInputs', module=PackDetInputs)
                except Exception:
                    # 如果注册失败，尝试重新注册（可能已有实例）
                    pass
            
            # 特殊处理：LetterResize 需要注册到多个 TRANSFORMS 注册表
            if 'LetterResize' not in MYOLO_TRANSFORMS.module_dict:
                MYOLO_TRANSFORMS.register_module(name='LetterResize', module=LetterResize)
            if 'LetterResize' not in MMDET_TRANSFORMS.module_dict:
                MMDET_TRANSFORMS.register_module(name='LetterResize', module=LetterResize)
            
            # 使用mmengine的配置加载机制
            from mmengine.config import Config
            from mmengine.registry import MODELS as GLOBAL_MODELS
            
            # 加载配置文件
            cfg = Config.fromfile(config_path)
            
            # 递归遍历配置，将带有 iou_mode 参数的 IoULoss 替换为 CompatibleIoULoss
            def replace_iou_loss(config):
                if isinstance(config, dict):
                    if config.get('type') == 'IoULoss' and 'iou_mode' in config:
                        # 将 IoULoss 替换为 CompatibleIoULoss
                        config['type'] = 'CompatibleIoULoss'
                    else:
                        for key, value in config.items():
                            if isinstance(value, (dict, list)):
                                replace_iou_loss(value)
                elif isinstance(config, list):
                    for item in config:
                        if isinstance(item, (dict, list)):
                            replace_iou_loss(item)
            
            # 修改模型配置中的损失函数
            replace_iou_loss(cfg.model)
            
            # 构建模型
            self.model = GLOBAL_MODELS.build(cfg.model)
            
            # 加载检查点
            from mmengine.runner.checkpoint import load_checkpoint
            load_checkpoint(self.model, checkpoint_path, map_location=self.device)
            
            # 设置模型为评估模式
            self.model.eval()
            self.model.to(self.device)
        except KeyError as e:
            print(f"❌ 模型注册错误: {e}")
            print("💡 提示: 请确保已正确安装 Mamba-YOLO-World 及其依赖项")
            print("   以及配置文件中指定的模型类型存在于yolo_world模块中")
            # 如果直接加载失败，尝试使用临时配置文件方式
            print("🔄 尝试使用备用加载方法...")
            
            # 备用方法：显式注册所有必要的模块后再加载
            from mmdet.registry import MODELS as MMDET_MODELS
            
            # 再次尝试导入所有需要的组件
            from yolo_world.models.detectors.yolo_world import YOLOWorldDetector
            from yolo_world.models.data_preprocessors.data_preprocessor import YOLOWDetDataPreprocessor
            from yolo_world.models.backbones.mm_backbone import MultiModalYOLOBackbone
            from yolo_world.models.necks.mamba_yolo_world_pafpn import MambaYOLOWorldPAFPN
            from yolo_world.models.dense_heads.yolo_world_head import YOLOWorldHead, YOLOWorldHeadModule
            from yolo_world.models.backbones.mm_backbone import HuggingCLIPLanguageBackbone  # 文本编码器
            from yolo_world.models.layers.mamba2_yolo_bricks import MambaFusionCSPLayerWithTwoConv2, TextGuidedODSSBlock2, TextGuidedSS2D2  # Mamba特殊层
            from yolo_world.models.layers.mamba2_simple import Mamba2Simple  # Mamba2简化版本
            
            # 导入基础的mmyolo组件（根据Mamba-YOLO-World配置文件的依赖）
            from mmyolo.models.backbones.csp_darknet import YOLOv8CSPDarknet
            from mmyolo.models.layers.yolo_bricks import SPPFBottleneck, CSPResLayer
            from mmyolo.models.data_preprocessors import YOLOv5DetDataPreprocessor
            
            # 导入并注册损失函数组件
            from mmdet.models.losses.iou_loss import IoULoss, BoundedIoULoss, GIoULoss, DIoULoss, CIoULoss
            from mmyolo.models.losses import IoULoss as YOLOv5IoULoss
            
            # 确保所有模块都被注册
            components_to_register = [
                ('YOLOWorldDetector', YOLOWorldDetector),
                ('YOLOWDetDataPreprocessor', YOLOWDetDataPreprocessor),
                ('MultiModalYOLOBackbone', MultiModalYOLOBackbone),
                ('MambaYOLOWorldPAFPN', MambaYOLOWorldPAFPN),
                ('YOLOWorldHead', YOLOWorldHead),
                ('YOLOWorldHeadModule', YOLOWorldHeadModule),
                # 文本编码器
                ('HuggingCLIPLanguageBackbone', HuggingCLIPLanguageBackbone),
                # Mamba特殊层
                ('MambaFusionCSPLayerWithTwoConv2', MambaFusionCSPLayerWithTwoConv2),
                ('TextGuidedODSSBlock2', TextGuidedODSSBlock2),
                ('TextGuidedSS2D2', TextGuidedSS2D2),
                ('Mamba2Simple', Mamba2Simple),
                # mmyolo组件
                ('YOLOv8CSPDarknet', YOLOv8CSPDarknet),
                ('SPPFBottleneck', SPPFBottleneck),
                ('CSPResLayer', CSPResLayer),
                ('YOLOv5DetDataPreprocessor', YOLOv5DetDataPreprocessor),
                # 损失函数组件
                ('IoULoss', IoULoss),
                ('BoundedIoULoss', BoundedIoULoss),
                ('GIoULoss', GIoULoss),
                ('DIoULoss', DIoULoss),
                ('CIoULoss', CIoULoss),
                ('YOLOv5IoULoss', YOLOv5IoULoss),
                # 兼容性损失函数
                ('CompatibleIoULoss', CompatibleIoULoss)
            ]
            
            for name, module in components_to_register:
                if name not in MMDET_MODELS.module_dict:
                    MMDET_MODELS.register_module(name=name, module=module)
            
            # 特殊处理：BatchTaskAlignedAssigner 需要注册到多个 TASK_UTILS 注册表
            if 'BatchTaskAlignedAssigner' not in MYOLO_TASK_UTILS.module_dict:
                MYOLO_TASK_UTILS.register_module(name='BatchTaskAlignedAssigner', module=BatchTaskAlignedAssigner)
            if 'BatchTaskAlignedAssigner' not in MMDET_TASK_UTILS.module_dict:
                MMDET_TASK_UTILS.register_module(name='BatchTaskAlignedAssigner', module=BatchTaskAlignedAssigner)
            
            # 重新尝试加载配置和构建模型
            from mmengine.config import Config
            from mmengine.registry import MODELS as GLOBAL_MODELS
            
            # 加载配置文件
            cfg = Config.fromfile(config_path)
            
            # 递归遍历配置，将带有 iou_mode 参数的 IoULoss 替换为 CompatibleIoULoss
            def replace_iou_loss(config):
                if isinstance(config, dict):
                    if config.get('type') == 'IoULoss' and 'iou_mode' in config:
                        # 将 IoULoss 替换为 CompatibleIoULoss
                        config['type'] = 'CompatibleIoULoss'
                    else:
                        for key, value in config.items():
                            if isinstance(value, (dict, list)):
                                replace_iou_loss(value)
                elif isinstance(config, list):
                    for item in config:
                        if isinstance(item, (dict, list)):
                            replace_iou_loss(item)
            
            # 修改模型配置中的损失函数
            replace_iou_loss(cfg.model)
            
            # 构建模型
            self.model = GLOBAL_MODELS.build(cfg.model)
            
            # 加载检查点
            from mmengine.runner.checkpoint import load_checkpoint
            load_checkpoint(self.model, checkpoint_path, map_location=self.device)
            
            # 设置模型为评估模式
            self.model.eval()
            self.model.to(self.device)
        except ImportError as e:
            print(f"⚠️ [Mamba-YOLO-World] 无法导入yolo-world模块: {e}")
            raise

        # 为推理构建一个简化的管道
        test_pipeline_cfg = [
            dict(type='mmdet.LoadImageFromNDArray'),
            dict(type='mmdet.Resize', scale=(640, 640), keep_ratio=True),
            dict(type='mmdet.LetterResize', scale=(640, 640), allow_scale_up=True, pad_val=dict(img=114)),
            dict(type='mmdet.Normalize', mean=[0., 0., 0.], std=[255., 255., 255.], to_rgb=True),
            dict(type='mmdet.PackDetInputs', meta_keys=('img_id', 'img_path', 'ori_shape', 'img_shape', 'scale_factor'))
        ]
        self.test_pipeline = Compose(test_pipeline_cfg)

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
        # 检查模型是否有reparameterize方法（特定于YOLO-World系列模型）
        if hasattr(self.model, 'reparameterize'):
            self.model.reparameterize(self.texts)
        else:
            # 对于某些模型变体，可能需要其他方式设置文本
            # 尝试使用set_text方法或其他类似方法
            if hasattr(self.model, 'set_text'):
                self.model.set_text(self.texts)
            elif hasattr(self.model, 'module') and hasattr(self.model.module, 'reparameterize'):
                # 如果是多GPU模型包装的情况
                self.model.module.reparameterize(self.texts)
            else:
                # 如果没有相应方法，记录警告
                print("⚠️ [Mamba-YOLO-World] 模型没有找到reparameterize方法，可能无法设置开放词汇检测类别")

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
