import threading
import traceback
import time
# todo: import yolo
from Yolov8 import Yolov8_Pose as yolo
#import sys
#sys.path.append(r"/Yolov8")
#import Yolov8_Pose as yolo
import cv2
import subprocess

from Yolov8.Yolov8_Pose import LoadPoseEngine
#from Yolov8_Pose import LoadPoseEngine
from Yolov8.main import LoadEngineModel
from service import AlarmService
#import AlarmService
from common import monitor as monitorCommon
#import monitor as monitorCommon
import copy


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
    infer1 = LoadEngineModel('algo/detcet3.engine')
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
                frame, warningList = yolo.main(infer=infer, infer1=infer1, np_img=frame, TYPE_LIST=monitorCommon.TYPE_LIST, AREA_LIST=monitorCommon.AREA_LIST)
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