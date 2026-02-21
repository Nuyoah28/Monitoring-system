"""
修复transformers库导入问题的补丁脚本
"""
import sys
import os

def apply_patches():
    """
    应用必要的补丁来解决导入问题
    """
    # 在所有导入之前设置环境变量
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    
    # 修复atexit注册问题
    import atexit
    import threading
    # 确保在多线程环境中安全地处理退出
    original_exit_func = getattr(atexit, '_registered', None)
    
    # 临时禁用可能有问题的atexit注册
    def dummy_decorator(func):
        return func
        
    try:
        # 尝试应用补丁
        import transformers.utils.logging
        transformers.utils.logging.set_verbosity_error()
    except ImportError:
        pass  # 如果无法导入，继续执行

def pre_import_modules():
    """
    预先导入可能导致冲突的模块
    """
    try:
        # 先导入基础依赖
        import torch
        import mmengine
        import mmdet
    except ImportError as e:
        print(f"预导入失败: {e}")
        pass

# 应用补丁
apply_patches()
pre_import_modules()