import os
import cv2
import mmcv
from mmdet.apis import init_detector, inference_detector
from mmdet.utils import register_all_modules
from mmengine.utils import track_iter_progress

# --- 关键路径配置 ---
CONFIG = 'algorithm/Mamba-YOLO-World/configs/mamba2_yolo_world_s_finetune_custom.py'
CHECKPOINT = 'algorithm/algo/best_coco_overflow_precision_epoch_90.pth'
# 你可以把这里的视频路径换成你自己的监控素材！
INPUT_VIDEO = 'algorithm/test_video/raw/fire.mp4' 
OUTPUT_VIDEO = 'algorithm/test_video/processed/fire.mp4'

def run_video_test():
    register_all_modules()
    os.makedirs(os.path.dirname(OUTPUT_VIDEO), exist_ok=True)
    
    # 1. 加载 100 轮冠军模型
    print(f"🧠 正在加载 89.6% 精度模型 (Epoch 100)...")
    model = init_detector(CONFIG, CHECKPOINT, device='cuda:0')
    
    # 2. 读取视频
    video_reader = mmcv.VideoReader(INPUT_VIDEO)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(
        OUTPUT_VIDEO, fourcc, video_reader.fps,
        (video_reader.width, video_reader.height))
    
    # 3. 逐帧检测并保存
    print(f"🔍 正在对视频进行深度检测...")
    for frame in track_iter_progress(video_reader):
        result = inference_detector(model, frame)
        
        # 可视化当前帧
        # 这里 score_thr=0.4 是置信度门限，你可以根据实际效果调整
        viz_frame = model.show_result(frame, result, score_thr=0.4, show=False)
        video_writer.write(viz_frame)
    
    video_writer.release()
    print(f"\n✅ 视频检测完成！结果已存入: {OUTPUT_VIDEO}")

if __name__ == '__main__':
    run_video_test()
