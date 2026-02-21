import threading
import traceback
import time
import os
from Yolov8 import Yolov8_Pose as yolo
import cv2
import subprocess

from Yolov8.Yolov8_Pose import LoadPoseEngine
# 将原来固定类别的 LoadEngineModel 替换为 Mamba-YOLO 开放词汇检测器
# from Yolov8.main import LoadEngineModel  # [已废弃] 原 TensorRT 烟火检测器
from Yolov8.mamba_yolo import MambaYOLODetector
from Yolov8.stgcn_action import ActionRecognizer
from service import AlarmService
from common import monitor as monitorCommon
import copy

# -----------------------------------------------------------------------
# Mamba-YOLO 自定义检测目标（在"火"和"烟"之外动态扩展）
# 顺序决定 class_id:
#   class_id=0  fire   (内置)
#   class_id=1  smoke  (内置)
#   class_id=2  garbage on ground     → caseType=8  垃圾乱放
#   class_id=3  ice on road           → caseType=9  冰面
#   class_id=4  electric scooter      → caseType=10 电动车进楼
#   class_id=5  vehicle on sidewalk   → caseType=11 载具占用车道
# -----------------------------------------------------------------------
CUSTOM_DETECTION_PROMPTS = [
    "garbage on ground",
    "ice on road",
    "electric scooter",
    "vehicle on sidewalk",
]


def stream_video():
    cap = cv2.VideoCapture(monitorCommon.STREAM_RAW_URL)
    # 设置摄像头分辨率
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)

    fps = cap.get(cv2.CAP_PROP_FPS)
    print("fps:", fps)
    # 设置缓冲区大小为2

    # 定义视频编码器
    fourcc = cv2.VideoWriter_fourcc(*'X264')

    # 创建FFmpeg命令行参数
    ffmpeg_cmd = ['ffmpeg',
                  '-y',  # 覆盖已存在的文件
                  '-f', 'rawvideo',
                  '-pixel_format', 'bgr24',
                  '-video_size', '640*480',
                  #'-re',
                  '-i', '-',  # 从标准输入读取数据
                  '-c:v', 'libx264',  # 使用x264编码器
                  '-preset', 'ultrafast',
                  '-tune', 'zerolatency',  # 零延迟
                  '-pix_fmt', 'yuv420p',
                  '-vf', 'scale=328:246',
                  '-f', 'flv',
                  '-r', '25',
                  #'-b:v', '500k',
                  monitorCommon.STREAM_PROCESSED_URL
                  ]
    # 启动Ffmpeg进程
    ffmepg_process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    counter = 0  # used for count subsequent frames
    # 模型加载
    infer = LoadPoseEngine('algo/yolov8n-pose.engine')
    # 用 Mamba-YOLO-World 开放词汇检测器替换原固定类别的 TensorRT 烟火检测器
    # -------------------------------------------------------------------
    # config_path:      Mamba-YOLO-World 的 mmyolo 配置文件
    # checkpoint_path:  从 HuggingFace 下载的 .pth 模型权重
    #                   https://huggingface.co/Xuan-World/Mamba-YOLO-World
    # -------------------------------------------------------------------
    MAMBA_YOLO_WORLD_ROOT = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'Mamba-YOLO-World')
    )
    infer1 = MambaYOLODetector(
        config_path=os.path.join(MAMBA_YOLO_WORLD_ROOT, 'configs', 'mamba2_yolo_world_s.py'),
        checkpoint_path='algo/mamba2_yolo_world_s.pth',   # 从 HuggingFace 下载后放这里
        confidence=0.3,
        extra_prompts=CUSTOM_DETECTION_PROMPTS
    )
    # ST-GCN++ 动作识别器 (替换 Yolov8_Pose.py 中的手写 if-else 规则)
    # 权重来源: PYSKL 官方 ST-GCN++ NTU-60 预训练权重
    action_recognizer = ActionRecognizer(
        checkpoint_path='algo/stgcnpp_ntu60.pth',
        buffer_size=30,
        confidence_threshold=0.5,
    )
    print('模型加载成功！')
    
    #设置时间
    post_delay = 20  # 延迟20秒
    last_post_time = time.time()  # 记录上一次post的时间
    

    # 开始采集和推流
    while True:
        # 采集一帧图像
        ret, frame = cap.read()
        while (not ret or not cap.isOpened()):
            print("读取帧失败或流未打开，正在重试...")
            cap.release()
            cap = cv2.VideoCapture(monitorCommon.STREAM_RAW_URL)
            ret,frame = cap.read()
        if ret:
            print('帧读取成功，开始处理')
            if monitorCommon.cacheQueue.qsize() < monitorCommon.cacheMax:
                monitorCommon.cacheQueue.put_nowait(frame)
                # print("put frame into queue " + str(monitorCommon.cacheQueue.qsize()))
            else:
                # print("queue is full")
                monitorCommon.cacheQueue.get_nowait()
                monitorCommon.cacheQueue.put_nowait(frame)
            # todo: 在这里进行图像处理
            try:
                frame, warningList = yolo.main(infer=infer, infer1=infer1, action_recognizer=action_recognizer, np_img=frame, TYPE_LIST=monitorCommon.TYPE_LIST, AREA_LIST=monitorCommon.AREA_LIST)
            except Exception as e:
                print(traceback.format_tb(e))
                continue
            print(warningList)
            current_time = time.time()
            if any(warningList) and current_time - last_post_time >= post_delay:
                AlarmService.postAlarm(copy.deepcopy(warningList))
                last_post_time = current_time

            # 通过Ffmpeg编码和推流
            ffmepg_process.stdin.write(frame.tobytes())
        else:
            continue
    # 停止Ffmpeg进程并释放资源
    ffmepg_process.stdin.close()
    ffmepg_process.wait()
    cap.release()
    # 在这里编写推流的代码
    print("开始推流")