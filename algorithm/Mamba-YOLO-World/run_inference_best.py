import os
from mmdet.apis import init_detector, inference_detector
from mmdet.utils import register_all_modules
import mmcv

# --- 关键路径配置 ---
CONFIG = 'algorithm/Mamba-YOLO-World/configs/mamba2_yolo_world_s_finetune_custom.py'
CHECKPOINT = 'algorithm/Mamba-YOLO-World/work_dirs/mamba2_yolo_world_s_finetune_custom/20260330_164108/best_coco_bbox_mAP_epoch_100.pth'
# 你可以把这里的图片换成你自己的！
TEST_IMAGE = 'algorithm/Mamba-YOLO-World/data/custom_finetune/images/val/000001.jpg' 
OUTPUT_DIR = 'algorithm/Mamba-YOLO-World/inference_results'

def run_test():
    register_all_modules()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f"🧠 正在加载最佳权重 (Epoch 90)...")
    model = init_detector(CONFIG, CHECKPOINT, device='cuda:0')
    
    print(f"🔍 正在执行 89.6% 精度的推理...")
    result = inference_detector(model, TEST_IMAGE)
    
    # 可视化并保存
    out_file = os.path.join(OUTPUT_DIR, 'result_best_model.jpg')
    model.show_result(TEST_IMAGE, result, out_file=out_file, score_thr=0.4)
    print(f"✅ 推理完成！结果已存入: {out_file}")

if __name__ == '__main__':
    run_test()
