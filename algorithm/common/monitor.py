from queue import Queue
from config import DevConfig as Config
from common.stream_config import CURRENT_STREAM_RAW_URL, CURRENT_STREAM_PROCESSED_URL

cacheQueue = Queue()
cacheMax = 250

# 使用动态流配置以支持不同的部署环境
STREAM_RAW_URL = CURRENT_STREAM_RAW_URL  # python后端拉原始流的地址
STREAM_PROCESSED_URL = CURRENT_STREAM_PROCESSED_URL  # python后端推处理之后的流的地址

# 添加新的配置项用于视频流处理
VIDEO_PROCESSING_ENABLED = True
VIDEO_CACHE_SIZE = 50

# -----------------------------------------------------------------------
# TYPE_LIST: 检测能力开关列表
# 顺序严格对应数据库 case_type_info 表 (caseType 1~12)
# 由 Java 后端通过 /api/v1/monitor-device/type 接口下发
#
#   索引  caseType  含义              当前检测方式
#   [0]     1      进入危险区域       姿态估计(禁区坐标判定)
#   [1]     2      烟雾              Mamba-YOLO (class_id=1, smoke)
#   [2]     3      区域停留          暂未实现
#   [3]     4      摔倒              ST-GCN++ 动作识别
#   [4]     5      明火              Mamba-YOLO (class_id=0, fire)
#   [5]     6      吸烟              暂未实现
#   [6]     7      打架              ST-GCN++ 动作识别
#   [7]     8      垃圾乱放          Mamba-YOLO (extra_prompt)
#   [8]     9      冰面              Mamba-YOLO (extra_prompt)
#   [9]    10      电动车进楼         Mamba-YOLO (extra_prompt)
#  [10]    11      载具占用车道       Mamba-YOLO (extra_prompt)
#  [11]    12      挥手呼救          ST-GCN++ 动作识别
# -----------------------------------------------------------------------
TYPE_LIST = [False, False, False, True, False, False, True, False, False, False, False, True]

# 左上 右下
AREA_LIST = [(0, 0), (1280, 720)]

capture_width = 1280
capture_height = 720
display_width = 1280
display_height = 720
framerate = 60
flip_method = 0
# ST-GCN++ maintains its own internal buffer, so preList only needs
# danger zone + Mamba-YOLO state (indices_danger, fire_indices, smoke_indices)
preList = [None, None, None]

