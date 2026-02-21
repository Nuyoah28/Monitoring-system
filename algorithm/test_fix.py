"""
测试修复后的Mamba-YOLO-World模型加载
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 应用导入补丁
from fix_imports import apply_patches
apply_patches()

print("正在测试模型导入...")

try:
    # 测试基本导入
    import torch
    import numpy as np
    print("✓ PyTorch 导入成功")
    
    import mmcv
    import mmengine
    print("✓ MMCV/MMEngine 导入成功")
    
    import mmdet
    print("✓ MMDetection 导入成功")
    
    # 尝试导入Mamba-YOLO检测器
    from Yolov8.mamba_yolo import MambaYOLODetector
    print("✓ MambaYOLODetector 导入成功")
    
    print("\n所有导入测试通过！")
    print(f"PyTorch 版本: {torch.__version__}")
    if hasattr(mmcv, '__version__'):
        print(f"MMCV 版本: {mmcv.__version__}")
    if hasattr(mmengine, '__version__'):
        print(f"MMEngine 版本: {mmengine.__version__}")
    if hasattr(mmdet, '__version__'):
        print(f"MMDetection 版本: {mmdet.__version__}")
    
except Exception as e:
    print(f"✗ 导入测试失败: {e}")
    import traceback
    traceback.print_exc()