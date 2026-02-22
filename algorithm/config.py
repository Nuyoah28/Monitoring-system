# name of config can only UpperCase
class Config:
    BACKEND_URL = ""# java后端
    STREAM_URL = ""# 流地址
    TOKEN = None
    MONITOR_ID = -1
    LATITUDE = 0
    LONGITUDE = 0
    TYPE_LIST = []
    AREA_LIST = []


class DevConfig(Config):
    BACKEND_URL = "http://localhost:10115"
    # 当videoProcess.py运行在Docker容器中时，需要连接到宿主机的RTMP服务器
    # 在Docker容器中，host.docker.internal通常指向宿主机
    STREAM_URL = "rtmp://host.docker.internal:1935"
    TOKEN = None
    
    # 腾讯云机器翻译 (TMT) 密钥配置
    # 请从腾讯云控制台获取: https://console.cloud.tencent.com/cam/capi
    TENCENT_SECRET_ID = "REMOVED"
    TENCENT_SECRET_KEY = "REMOVED"
    
    pass


class ProdConfig(Config):
    TOKEN = None


config = {
    "dev": DevConfig,
    "prod": ProdConfig
}

