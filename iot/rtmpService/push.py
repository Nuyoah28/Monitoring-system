import cv2
import av
import time

# 配置参数
RTMP_URL = "rtmp://192.168.213.197:1935/live/raw"  # 您的RTMP目标地址
CAMERA_INDEX = 0  # 默认摄像头索引，通常0是内置摄像头。如果是USB摄像头，可能需要尝试1,2等。
FRAME_RATE = 30  # 帧率
RESOLUTION = (1280, 720)  # 分辨率 (宽度, 高度)

def main():
    # 1. 初始化摄像头
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("错误：无法打开摄像头。请检查索引或连接。")
        return

    # 设置摄像头参数（非所有摄像头都支持）
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUTION[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUTION[1])
    cap.set(cv2.CAP_PROP_FPS, FRAME_RATE)

    # 2. 初始化PyAV输出容器和流
    output_container = av.open(RTMP_URL, mode='w', format='flv')
    stream = output_container.add_stream('h264', rate=FRAME_RATE)
    stream.width = RESOLUTION[0]
    stream.height = RESOLUTION[1]
    stream.pix_fmt = 'yuv420p'
    stream.options = {
        'tune': 'zerolatency',  # 低延迟编码
        'preset': 'ultrafast'    # 快速编码
    }

    print(f"开始向 {RTMP_URL} 推流... (按 Ctrl+C 停止)")

    try:
        frame_count = 0
        start_time = time.time()
        while True:
            # 3. 从摄像头读取一帧
            ret, frame = cap.read()
            if not ret:
                print("错误：无法从摄像头读取帧。")
                break

            # 4. 将OpenCV的BGR帧转换为PyAV的视频帧 (BGR -> RGB -> YUV420P)
            # OpenCV 默认是 BGR 顺序，需要转换为 RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            av_frame = av.VideoFrame.from_ndarray(frame_rgb, format='rgb24')
            av_frame = av_frame.reformat(width=stream.width, height=stream.height, format=stream.pix_fmt)
            av_frame.pts = frame_count  # 设置显示时间戳

            # 5. 编码并发送数据包
            for packet in stream.encode(av_frame):
                output_container.mux(packet)
            
            frame_count += 1

            # 可选：在本地窗口显示预览
            # cv2.imshow('Live Stream Preview', frame)
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #    break

    except KeyboardInterrupt:
        print("\n收到中断信号，正在停止...")
    finally:
        # 6. 刷新编码器并写入尾包
        for packet in stream.encode():
            output_container.mux(packet)
        # 7. 清理资源
        output_container.close()
        cap.release()
        cv2.destroyAllWindows()
        elapsed_time = time.time() - start_time
        if elapsed_time > 0:
            print(f"推流结束。共推送 {frame_count} 帧，平均帧率：{frame_count / elapsed_time:.2f} fps")

if __name__ == "__main__":
    main()