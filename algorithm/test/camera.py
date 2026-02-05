#!/usr/bin/env python3
"""
简化版摄像头推流脚本
"""

import cv2
import subprocess
import signal
import sys
import time


def signal_handler(sig, frame):
    print("\n正在停止推流...")
    sys.exit(0)


def main():
    # RTMP服务器地址
    RTMP_URL = "rtmp://localhost:1935/live/ai"

    # 摄像头参数
    CAMERA_INDEX = 1
    FPS = 30
    WIDTH = 640
    HEIGHT = 480

    print(f"推流到: {RTMP_URL}")
    print(f"摄像头: {CAMERA_INDEX}")
    print(f"分辨率: {WIDTH}x{HEIGHT}")
    print(f"帧率: {FPS}")
    print("按 Ctrl+C 停止")

    # 打开摄像头
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("错误: 无法打开摄像头")
        return

    # 设置摄像头参数
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, FPS)

    # FFmpeg命令
    command = [
        'ffmpeg',
        '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-pix_fmt', 'bgr24',
        '-s', f'{WIDTH}x{HEIGHT}',
        '-r', str(FPS),
        '-i', '-',
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-preset', 'ultrafast',
        '-f', 'flv',
        RTMP_URL
    ]

    # 启动FFmpeg进程
    process = subprocess.Popen(command, stdin=subprocess.PIPE)

    # 设置中断处理
    signal.signal(signal.SIGINT, signal_handler)

    frame_count = 0
    start_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("错误: 无法读取帧")
                break

            # 写入到FFmpeg
            process.stdin.write(frame.tobytes())

            # 显示预览
            cv2.imshow('Camera Stream', frame)

            # 按q退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # 统计
            frame_count += 1
            if frame_count % 100 == 0:
                elapsed = time.time() - start_time
                fps = frame_count / elapsed
                print(f"已发送 {frame_count} 帧, FPS: {fps:.2f}")

    except Exception as e:
        print(f"错误: {e}")
    finally:
        # 清理
        cap.release()
        cv2.destroyAllWindows()
        if process:
            process.stdin.close()
            process.wait()
        print("推流已停止")


if __name__ == "__main__":
    main()