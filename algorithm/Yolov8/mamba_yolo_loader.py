"""Model loading helpers for Mamba-YOLO-World.

This module contains the original model registration, checkpoint loading, and
inference pipeline construction logic extracted from ``mamba_yolo.py``. It
mutates the detector instance exactly like the previous inline constructor code
did, so model structure, weights, preprocessing, and inference behavior stay the
same.
"""

import os
import sys


def load_model_and_pipeline(detector, config_path: str, checkpoint_path: str):
    """Load model and test pipeline onto an existing MambaYOLODetector."""
    self = detector
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
        from mmyolo.datasets.transforms.transforms import LetterResize, YOLOv5KeepRatioResize
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
        if 'YOLOv5KeepRatioResize' not in MYOLO_TRANSFORMS.module_dict:
            MYOLO_TRANSFORMS.register_module(name='YOLOv5KeepRatioResize', module=YOLOv5KeepRatioResize)
        if 'YOLOv5KeepRatioResize' not in MMDET_TRANSFORMS.module_dict:
            MMDET_TRANSFORMS.register_module(name='YOLOv5KeepRatioResize', module=YOLOv5KeepRatioResize)
    
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
        if 'YOLOv5KeepRatioResize' not in MYOLO_TRANSFORMS.module_dict:
            MYOLO_TRANSFORMS.register_module(name='YOLOv5KeepRatioResize', module=YOLOv5KeepRatioResize)
        if 'YOLOv5KeepRatioResize' not in MMDET_TRANSFORMS.module_dict:
            MMDET_TRANSFORMS.register_module(name='YOLOv5KeepRatioResize', module=YOLOv5KeepRatioResize)
    
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

    # Build an ndarray pipeline aligned with the official Mamba-YOLO-World demo.
    # The model data_preprocessor handles /255 and BGR->RGB; doing Normalize
    # here would normalize twice and can suppress detections.
    test_pipeline_cfg = [
        dict(type='mmdet.LoadImageFromNDArray'),
        dict(type='mmdet.YOLOv5KeepRatioResize', scale=(640, 640)),
        dict(type='mmdet.LetterResize', scale=(640, 640), allow_scale_up=False, pad_val=dict(img=114)),
        dict(
            type='mmdet.PackDetInputs',
            meta_keys=('img_id', 'img_path', 'ori_shape', 'img_shape', 'scale_factor', 'pad_param')
        )
    ]
    self.test_pipeline = Compose(test_pipeline_cfg)

