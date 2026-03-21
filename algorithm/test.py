import cv2
import subprocess
import time

# 打开本地摄像头
cap = cv2.VideoCapture(1)

# 检查摄像头是否成功打开
if not cap.isOpened():
    print("无法打开摄像头")
    exit()

# 设置摄像头参数
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

# FFmpeg命令配置
rtmp_url = "rtmp://localhost:1935/live/raw"
ffmpeg_cmd = [
    'ffmpeg',
    '-f', 'rawvideo',
    '-pix_fmt', 'bgr24',
    '-s', '640x480',
    '-r', '30',  # 输入帧率
    '-i', '-',   # 从stdin读取
    '-c:v', 'libx264',
    '-pix_fmt', 'yuv420p',
    '-preset', 'ultrafast',
    '-tune', 'zerolatency',
    '-f', 'flv',
    '-r', '30',  # 输出帧率
    rtmp_url
]

try:
    # 启动FFmpeg进程
    process = None
    retry_count = 0
    max_retries = 3

    # 等待RTMP服务器准备就绪
    print("等待RTMP服务器准备就绪...")
    time.sleep(5)  # 增加等待时间到5秒

    while retry_count < max_retries:
        try:
            process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"开始向 {rtmp_url} 推流...")
            break
        except FileNotFoundError:
            print("错误：找不到ffmpeg命令，请确保已安装ffmpeg并添加到系统PATH中")
            exit(1)
        except Exception as e:
            print(f"FFmpeg启动失败 ({retry_count+1}/{max_retries}): {e}")
            retry_count += 1
            time.sleep(3)  # 增加等待时间

    while True:
        ret, frame = cap.read()
        if not ret:
            print("无法读取摄像头帧，正在重试...")
            time.sleep(1)
            continue
            
        try:
            # 将帧数据写入FFmpeg进程
            process.stdin.write(frame.tobytes())
        except BrokenPipeError:
            print("FFmpeg进程管道断开，重新启动...")
            process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
            continue
        except Exception as e:
            print(f"写入FFmpeg进程出错: {e}")
            break

except Exception as e:
    print(f"FFmpeg推流过程中出现错误: {e}")

finally:
    # 清理资源
    if 'process' in locals():
        process.stdin.close()
        process.wait()
    cap.release()
    print("资源清理完成")