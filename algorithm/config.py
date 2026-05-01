# name of config can only UpperCase
class Config:
    BACKEND_URL = ""# java后端
    STREAM_URL = ""# 流地址
    STREAM_RAW_URL = ""# python后端拉原始流地址
    STREAM_PROCESSED_URL = ""# python后端推处理后流地址
    TOKEN = None
    MONITOR_ID = 1  # 默认演示点位；接入新摄像头时改成 monitor 表里的真实 id
    LATITUDE = 0
    LONGITUDE = 0
    TYPE_LIST = []
    AREA_LIST = []
    ALARM_CACHE_ENABLED = True
    ALARM_CACHE_DIR = "runtime/alarm_cache"
    ALARM_CACHE_DB = "alarm_cache.sqlite3"
    ALARM_CACHE_CLIP_DIR = "clips"
    ALARM_SYNC_INTERVAL_SECONDS = 10
    ALARM_SYNC_BATCH_SIZE = 20
    ALARM_REQUEST_TIMEOUT_SECONDS = 5


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
