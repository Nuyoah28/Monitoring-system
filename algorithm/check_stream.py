"""
RTMP流状态检查脚本
用于验证RTMP流是否真正可用
"""

import cv2
import time

def check_rtmp_stream(stream_url):
    """检查RTMP流是否可用"""
    print(f"正在检查流: {stream_url}")
    
    # 尝试连接到流
    cap = cv2.VideoCapture(stream_url)
    
    # 设置一些参数以改善连接
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    # 尝试读取几帧以确认流是活动的
    success_count = 0
    max_attempts = 10  # 尝试读取10次
    
    for i in range(max_attempts):
        ret, frame = cap.read()
        if ret:
            success_count += 1
            print(f"成功读取第 {i+1} 帧 (尺寸: {frame.shape})")
        else:
            print(f"第 {i+1} 次读取失败")
        
        time.sleep(0.5)  # 等待0.5秒再试
    
    cap.release()
    
    print(f"\n结果: 成功读取 {success_count}/{max_attempts} 帧")
    
    if success_count > 0:
        print("✓ 流可用")
        return True
    else:
        print("✗ 流不可用")
        return False

def main():
    # 检查原始流
    raw_stream_url = "rtmp://localhost:1935/live/raw"
    print("=" * 50)
    print("RTMP流状态检查")
    print("=" * 50)
    
    check_rtmp_stream(raw_stream_url)
    
    print("\n如果流不可用，请检查:")
    print("1. test.py 是否正在运行并向该地址推送")
    print("2. RTMP服务器是否正确配置")
    print("3. 网络连接是否正常")

if __name__ == "__main__":
    main()