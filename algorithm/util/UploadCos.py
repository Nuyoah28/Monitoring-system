import cv2
import subprocess
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from util import Logger
import queue
import threading
from config import RuntimeConfig as Config

logger = Logger.setup_logger()

SECRET_ID = Config.TENCENT_SECRET_ID
SECRET_KEY = Config.TENCENT_SECRET_KEY
REGION = Config.TENCENT_COS_REGION
BUCKET = Config.TENCENT_COS_BUCKET


def _require_cos_config():
    missing = []
    if not SECRET_ID:
        missing.append("TENCENT_SECRET_ID")
    if not SECRET_KEY:
        missing.append("TENCENT_SECRET_KEY")
    if not BUCKET:
        missing.append("TENCENT_COS_BUCKET")
    if missing:
        raise RuntimeError("missing COS config: " + ", ".join(missing))


def _cos_client():
    _require_cos_config()
    cos_config = CosConfig(Region=REGION, SecretId=SECRET_ID, SecretKey=SECRET_KEY)
    return CosS3Client(cos_config)


def uploadFile2Cos(file_path, uuid):
    object_key = uuid + '.flv'
    cos_client = _cos_client()
    with open(file_path, 'rb') as file_obj:
        cos_client.put_object(Bucket=BUCKET, Key=object_key, Body=file_obj)
    print("upload success" + str(uuid))


def buildFlvBytes(list):
    cnt = 0

    # 创建一个缓存列表，用于存储每一帧的字节流
    frame_list = []

    while cnt != len(list):
        frame = list[cnt]
        _, jpeg_frame = cv2.imencode('.jpg', frame)
        image_bytes = jpeg_frame.tobytes()
        # 将编码后的帧数据添加到缓存列表
        frame_list.append(image_bytes)
        cnt += 1
    logger.info("get frame list")
    video_bytes = b''.join(frame_list)
    command = ['ffmpeg', '-i', 'pipe:0', '-c:v', 'libx264', '-f', 'flv', 'pipe:1']
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("111111111111111")
    # 创建队列用于存储输出流
    output_queue = queue.Queue()

    # 定义函数用于读取子进程的输出流
    def read_output():
        while True:
            print("reading!!!")
            output = process.stdout.read(4096)
            if output:
                output_queue.put(output)
            else:
                break

    # 创建线程读取子进程的输出流
    print("22222222222")
    output_thread = threading.Thread(target=read_output)
    output_thread.start()
    print("3333333333")
    # 将输入流写入FFmpeg的标准输入流
    process.stdin.write(video_bytes)
    print("555555555555")
    process.stdin.close()
    # 等待子进程完成
    process.wait()

    # 等待输出线程结束
    output_thread.join()
    # 从队列中读取输出流
    output_stream = b''
    while not output_queue.empty():
        output_stream += output_queue.get()
    return output_stream


def saveFrames2Flv(list, file_path):
    output_stream = buildFlvBytes(list)
    with open(file_path, 'wb') as file_obj:
        file_obj.write(output_stream)


def upload2Cos(list,uuid):
    # 配置腾讯云COS服务 !!!!!!!!!!!!!!!!!!!!
    cos_client = _cos_client()
    output_stream = buildFlvBytes(list)
    # 上传字节流到腾讯云COS服务
    object_key = uuid + '.flv'  # 上传的对象键
    cos_client.put_object(Bucket=BUCKET, Key=object_key, Body=output_stream)
    print("upload success"+str(uuid))
