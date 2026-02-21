"""
简化版测试脚本，绕过RTMP服务器直接在内存中传递视频帧
用于测试AI检测算法而不依赖外部RTMP服务器
"""

import cv2
import time
import threading
import queue
from Yolov8 import Yolov8_Pose as yolo
from Yolov8.mamba_yolo import MambaYOLODetector
from Yolov8.stgcn_action import ActionRecognizer
from service import AlarmService
from common import monitor as monitorCommon
import copy
import traceback
import os

# 首先应用导入补丁
from fix_imports import apply_patches
apply_patches()

# 创建全局队列用于在内存中传递帧
frame_queue = queue.Queue(maxsize=10)  # 限制队列大小避免内存溢出

def camera_thread():
    """摄像头捕获线程"""
    # 尝试打开本地摄像头
    cap = cv2.VideoCapture(0)  # 尝试摄像头索引0
    
    if not cap.isOpened():
        print("无法打开本地摄像头，尝试虚拟摄像头...")
        # 如果物理摄像头不可用，创建测试画面
        cap = None
    else:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        print("成功打开本地摄像头")
    
    frame_count = 0
    while True:
        if cap is not None:
            ret, frame = cap.read()
            if not ret:
                print("无法读取摄像头帧")
                time.sleep(0.1)
                continue
        else:
            # 创建测试画面
            frame = create_test_frame(640, 480)
        
        # 将帧放入队列（非阻塞）
        try:
            if frame_queue.full():
                frame_queue.get_nowait()  # 移除旧帧
            frame_queue.put_nowait(frame)
        except queue.Full:
            continue  # 如果队列满，跳过此帧
        
        frame_count += 1
        if frame_count % 30 == 0:  # 每30帧打印一次
            print(f"已捕获 {frame_count} 帧")
        
        time.sleep(1/30)  # 控制帧率

def create_test_frame(width=640, height=480):
    """创建测试画面"""
    import numpy as np
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    # 创建一个移动的矩形作为测试图案
    cv2.rectangle(frame, (50, 50), (100, 100), (0, 255, 0), -1)
    cv2.putText(frame, 'TEST FRAME', (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    return frame

def processing_thread():
    """AI处理线程"""
    print("正在加载AI模型...")
    
    # 模型加载
    try:
        infer = yolo.LoadPoseEngine('algo/yolov8n-pose.engine')
    except:
        print("无法加载YoloV8 Pose模型")
        return
    
    # Mamba-YOLO-World 模型
    MAMBA_YOLO_WORLD_ROOT = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'Mamba-YOLO-World')
    )
    CUSTOM_DETECTION_PROMPTS = [
        "garbage on ground",
        "ice on road", 
        "electric scooter",
        "vehicle on sidewalk",
    ]
    
    try:
        infer1 = MambaYOLODetector(
            config_path=os.path.join(MAMBA_YOLO_WORLD_ROOT, 'configs', 'mamba2_yolo_world_s.py'),
            checkpoint_path='algo/mamba2_yolo_world_s.pth',
            confidence=0.3,
            extra_prompts=CUSTOM_DETECTION_PROMPTS
        )
    except Exception as e:
        print(f"无法加载Mamba-YOLO模型: {e}")
        return
    
    # ST-GCN++ 动作识别器
    try:
        action_recognizer = ActionRecognizer(
            checkpoint_path='algo/stgcnpp_ntu60.pth',
            buffer_size=30,
            confidence_threshold=0.5,
        )
        print('AI模型加载成功！')
    except Exception as e:
        print(f"无法加载ST-GCN++模型: {e}")
        return
    
    # 设置时间延迟
    post_delay = 20
    last_post_time = time.time()
    
    frame_count = 0
    
    while True:
        try:
            # 从队列获取帧
            frame = frame_queue.get(timeout=1)
            
            # 处理帧
            try:
                processed_frame, warningList = yolo.main(
                    infer=infer, 
                    infer1=infer1, 
                    action_recognizer=action_recognizer, 
                    np_img=frame, 
                    TYPE_LIST=monitorCommon.TYPE_LIST, 
                    AREA_LIST=monitorCommon.AREA_LIST
                )
                
                print(f"处理结果: {warningList}")
                
                current_time = time.time()
                if any(warningList) and current_time - last_post_time >= post_delay:
                    AlarmService.postAlarm(copy.deepcopy(warningList))
                    last_post_time = current_time
                    
            except Exception as e:
                print(f"帧处理错误: {e}")
                traceback.print_exc()
                
            frame_count += 1
            if frame_count % 30 == 0:  # 每30帧打印一次
                print(f"已处理 {frame_count} 帧")
                
        except queue.Empty:
            continue  # 队列为空，继续循环
        except KeyboardInterrupt:
            print("处理被用户中断")
            break

def main():
    print("启动简化版视频流处理系统...")
    print("此版本绕过RTMP服务器，直接在内存中传递视频帧")
    
    # 启动摄像头线程
    cam_thread = threading.Thread(target=camera_thread, daemon=True)
    cam_thread.start()
    
    # 启动处理线程
    proc_thread = threading.Thread(target=processing_thread, daemon=True)
    proc_thread.start()
    
    try:
        # 主线程等待
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("程序被用户中断")

if __name__ == "__main__":
    main()