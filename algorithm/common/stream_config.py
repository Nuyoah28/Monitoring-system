"""
Docker环境下的流媒体配置管理
用于处理跨容器通信的流地址配置
"""

import os

def get_stream_config():
    """
    根据运行环境返回适当的流配置
    """
    # 检查环境变量来确定运行环境
    env_type = os.getenv('RUN_ENV', 'default')
    
    if env_type == 'docker-video-process':
        # 当videoProcess.py在独立的Docker容器中运行时
        return {
            'STREAM_URL': 'rtmp://rtmp-server:1935',  # 连接到RTMP服务器容器
            'STREAM_RAW_URL': 'rtmp://rtmp-server:1935/live/raw',
            'STREAM_PROCESSED_URL': 'rtmp://rtmp-server:1935/live/ai'
        }
    elif env_type == 'docker-rtmp-server':
        # 当在RTMP服务器容器中运行时
        return {
            'STREAM_URL': 'rtmp://localhost:1935',
            'STREAM_RAW_URL': 'rtmp://localhost:1935/live/raw',
            'STREAM_PROCESSED_URL': 'rtmp://localhost:1935/live/ai'
        }
    else:
        # 默认配置（支持Docker容器访问宿主机）
        custom_rtmp_host = os.getenv('RTMP_HOST', 'host.docker.internal')
        custom_rtmp_port = os.getenv('RTMP_PORT', '1935')
        return {
            'STREAM_URL': f'rtmp://{custom_rtmp_host}:{custom_rtmp_port}',
            'STREAM_RAW_URL': f'rtmp://{custom_rtmp_host}:{custom_rtmp_port}/live/raw',
            'STREAM_PROCESSED_URL': f'rtmp://{custom_rtmp_host}:{custom_rtmp_port}/live/ai'
        }

def get_current_stream_raw_url():
    """
    获取当前环境下的原始流URL
    """
    env_type = os.getenv('RUN_ENV', 'default')
    
    if env_type == 'docker-video-process':
        return 'rtmp://rtmp-server:1935/live/raw'
    else:
        # 检查是否有自定义的RTMP服务器地址
        # 优先使用host.docker.internal以支持Docker容器访问宿主机
        custom_rtmp_host = os.getenv('RTMP_HOST', 'host.docker.internal')
        custom_rtmp_port = os.getenv('RTMP_PORT', '1935')
        return f'rtmp://{custom_rtmp_host}:{custom_rtmp_port}/live/raw'

def get_current_stream_processed_url():
    """
    获取当前环境下的处理后流URL
    """
    env_type = os.getenv('RUN_ENV', 'default')
    
    if env_type == 'docker-video-process':
        return 'rtmp://rtmp-server:1935/live/ai'
    else:
        # 检查是否有自定义的RTMP服务器地址
        # 优先使用host.docker.internal以支持Docker容器访问宿主机
        custom_rtmp_host = os.getenv('RTMP_HOST', 'host.docker.internal')
        custom_rtmp_port = os.getenv('RTMP_PORT', '1935')
        return f'rtmp://{custom_rtmp_host}:{custom_rtmp_port}/live/ai'

# 为了兼容现有代码，提供一个可以直接使用的流URL
CURRENT_STREAM_RAW_URL = get_current_stream_raw_url()
CURRENT_STREAM_PROCESSED_URL = get_current_stream_processed_url()