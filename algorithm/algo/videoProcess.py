import threading
import traceback
import time
import os

# 首先应用导入补丁
from fix_imports import apply_patches
apply_patches()

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

# Mamba-YOLO 自定义检测目标（在"火"和"烟"之外动态扩展）
# 列表定义和更改标志位已移至 common.monitor 中，
# 并通过 controller/monitorController.py 的 /update_prompt 接口动态修改。
# -----------------------------------------------------------------------


def stream_video():
    # 增加重试连接机制
    max_retries = 30  # 最多重试30次
    retry_interval = 2  # 每隔2秒重试一次
    retry_count = 0
    
    cap = None
    while retry_count < max_retries:
        try:
            cap = cv2.VideoCapture(monitorCommon.STREAM_RAW_URL)
            if cap.isOpened():
                # 设置摄像头分辨率
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 减小缓冲区，降低延迟
                
                fps = cap.get(cv2.CAP_PROP_FPS)
                print(f"成功连接到视频流，FPS: {fps}")
                
                if fps > 0:  # 确认流是活动的
                    break
                else:
                    print("连接到流但无法获取FPS，重试...")
                    cap.release()
            else:
                print(f"无法连接到视频流: {monitorCommon.STREAM_RAW_URL}")
                
        except Exception as e:
            print(f"连接视频流时出错 ({retry_count+1}/{max_retries}): {e}")
        
        retry_count += 1
        print(f"等待 {retry_interval} 秒后重试... ({retry_count}/{max_retries})")
        time.sleep(retry_interval)
    
    if retry_count >= max_retries:
        print("达到最大重试次数，无法连接到视频流")
        return
    
    # 确认视频流确实可读
    ret, test_frame = cap.read()
    if not ret:
        print("连接到流但无法读取帧，持续重试...")
        while not ret and retry_count < max_retries * 2:
            time.sleep(1)
            cap.release()
            cap = cv2.VideoCapture(monitorCommon.STREAM_RAW_URL)
            ret, test_frame = cap.read()
            retry_count += 1
        if not ret:
            print("仍然无法读取帧，退出")
            return

    # 定义视频编码器
    fourcc = cv2.VideoWriter_fourcc(*'X264')

    # 创建FFmpeg命令行参数
    ffmpeg_cmd = ['ffmpeg',
                  '-y',  # 覆盖已存在的文件
                  '-f', 'rawvideo',
                  '-pixel_format', 'bgr24',
                  '-video_size', '640x480',  # 修正尺寸格式，使用 x 而不是 *
                  '-i', '-',  # 从标准输入读取数据
                  '-c:v', 'libx264',  # 使用x264编码器
                  '-preset', 'ultrafast',
                  '-tune', 'zerolatency',  # 零延迟
                  '-pix_fmt', 'yuv420p',
                  '-vf', 'scale=328:246',
                  '-f', 'flv',
                  '-r', '25',
                  '-fflags', '+genpts',  # 生成PTS以避免时间戳错误
                  monitorCommon.STREAM_PROCESSED_URL
                  ]
    # 启动Ffmpeg进程，增加错误处理
    try:
        ffmepg_process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        print("错误：找不到ffmpeg命令，请确保已安装ffmpeg并添加到系统PATH中")
        return
    except Exception as e:
        print(f"启动FFmpeg进程时发生错误: {e}")
        return
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
        extra_prompts=monitorCommon.CUSTOM_DETECTION_PROMPTS
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
        try:
            ret, frame = cap.read()
        except:
            ret = False
            
        while (not ret or not cap.isOpened()):
            print("读取帧失败或流未打开，正在重试...")
            try:
                cap.release()
            except:
                pass
            # 使用带重试机制的方式重新连接
            temp_retry_count = 0
            max_temp_retries = 10
            while temp_retry_count < max_temp_retries:
                try:
                    cap = cv2.VideoCapture(monitorCommon.STREAM_RAW_URL)
                    ret, frame = cap.read()
                    if ret and cap.isOpened():
                        print("重新连接成功")
                        break
                    else:
                        cap.release()
                except Exception as e:
                    print(f"重连尝试 {temp_retry_count+1} 失败: {e}")
                
                temp_retry_count += 1
                time.sleep(2)
            
            if temp_retry_count >= max_temp_retries:
                print("达到最大重连尝试次数，退出")
                return  # 退出函数而不是继续循环以避免无限重试
                
        if ret:
            # print('帧读取成功，开始处理')
            
            # 动态更新 Mamba-YOLO 检测目标 (无需重启模型)
            if monitorCommon.PROMPTS_CHANGED:
                print(f"🔥 检测到前端指令更新，正在注入新的 Mamba-YOLO 目标: {monitorCommon.CUSTOM_DETECTION_PROMPTS}")
                infer1.set_custom_prompts(monitorCommon.CUSTOM_DETECTION_PROMPTS)
                monitorCommon.PROMPTS_CHANGED = False
                
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
                print(f"处理帧时出错: {e}")
                traceback.print_exc()
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