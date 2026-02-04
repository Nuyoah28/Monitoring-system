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
    STREAM_URL = "rtsp://localhost:1935"
    TOKEN = None
    pass


class ProdConfig(Config):
    TOKEN = None


config = {
    "dev": DevConfig,
    "prod": ProdConfig
}

