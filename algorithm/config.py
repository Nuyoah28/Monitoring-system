# name of config can only UpperCase
class Config:
    BACKEND_URL = ""# java后端
    STREAM_URL = ""# 流地址
    STREAM_RAW_URL = ""# python后端拉原始流地址
    STREAM_PROCESSED_URL = ""# python后端推处理后流地址
    TOKEN = None
    MONITOR_ID = -1
    LATITUDE = 0
    LONGITUDE = 0
    TYPE_LIST = []
    AREA_LIST = []


class DevConfig(Config):
    BACKEND_URL = "http://host.docker.internal:10215"
    STREAM_URL = "rtmp://host.docker.internal:1935"
    STREAM_RAW_URL = "rtmp://host.docker.internal:1935/live/raw"
    STREAM_PROCESSED_URL = "rtmp://host.docker.internal:1935/live/ai"
    TOKEN = None
    
    # 腾讯云机器翻译 (TMT) 密钥配置
    # 请从腾讯云控制台获取: https://console.cloud.tencent.com/cam/capi
    # 使用环境变量，避免将敏感信息提交到代码仓库
    TENCENT_SECRET_ID = 'AKIDT7ufHm8NOF4IHdmkaJtaFxYyHe9f1XvB'
    TENCENT_SECRET_KEY = 'B9wWO8j9MYfdoqpeHhtth5HH3cy85pLd'
    
    pass


class ProdConfig(Config):
    TOKEN = None


config = {
    "dev": DevConfig,
    "prod": ProdConfig
}

