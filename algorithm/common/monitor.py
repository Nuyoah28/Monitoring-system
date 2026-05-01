import os
from queue import Queue
from config import DevConfig as Config

cacheQueue = Queue()
cacheMax = 250

STREAM_RAW_URL = Config.STREAM_RAW_URL  # python后端拉原始流的地址
STREAM_PROCESSED_URL = Config.STREAM_PROCESSED_URL  # python后端推处理之后的流的地址

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
#   [5]     6      吸烟              已停用
#   [6]     7      打架              ST-GCN++ 动作识别
#   [7]     8      垃圾乱放          Mamba-YOLO (extra_prompt)
#   [8]     9      冰面              已停用（Mamba 权重未针对冰面微调）
#   [9]    10      电动车进楼         Mamba-YOLO (extra_prompt)
#  [10]    11      载具占用车道       暂交由后续算法实现
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

# -----------------------------------------------------------------------
# Mamba-YOLO 自定义检测目标（在"火"和"烟"之外动态扩展）
# 这个列表会在 Flask 进程里修改，在 video stream 进程里被读取。
# -----------------------------------------------------------------------
CUSTOM_DETECTION_PROMPTS = [
    "overflow",
    "garbage",
    "garbage bin",
    "bicycle",
    "motorcycle",
]

# 标志位：提示词是否发生更改
PROMPTS_CHANGED = False

# Action-model runtime config. The defaults are tuned for the
# current CTR-GCN action weights (window=90, label order fixed).
ACTION_MODEL_BACKEND = os.environ.get("ACTION_MODEL_BACKEND", "ctrgcn").lower()
ACTION_CTR_GCN_ROOT = os.environ.get("ACTION_CTR_GCN_ROOT", "")
ACTION_CTR_GCN_WEIGHTS = os.environ.get("ACTION_CTR_GCN_WEIGHTS", "algo/ctrgcn_action4.pt")
ACTION_LABEL_ORDER = ("normal", "fall", "punch", "wave")
ACTION_WINDOW_SIZE = int(os.environ.get("ACTION_WINDOW_SIZE", "90"))
ACTION_MIN_FRAMES = int(os.environ.get("ACTION_MIN_FRAMES", "8"))
ACTION_SMOOTH = int(os.environ.get("ACTION_SMOOTH", "4"))
ACTION_MAX_TRACKS = int(os.environ.get("ACTION_MAX_TRACKS", "8"))
ACTION_TOP_K_TRACKS = int(os.environ.get("ACTION_TOP_K_TRACKS", "4"))
ACTION_INFER_INTERVAL = int(os.environ.get("ACTION_INFER_INTERVAL", "1"))
ACTION_MAX_MISSING = int(os.environ.get("ACTION_MAX_MISSING", "10"))

ACTION_FALL_ON_THR = float(os.environ.get("ACTION_FALL_ON_THR", "0.35"))
ACTION_FALL_OFF_THR = float(os.environ.get("ACTION_FALL_OFF_THR", "0.15"))
ACTION_FALL_HOLD_FRAMES = int(os.environ.get("ACTION_FALL_HOLD_FRAMES", "75"))
ACTION_FALL_RELEASE_FRAMES = int(os.environ.get("ACTION_FALL_RELEASE_FRAMES", "30"))

ACTION_WAVE_ON_THR = float(os.environ.get("ACTION_WAVE_ON_THR", "0.40"))
ACTION_WAVE_OFF_THR = float(os.environ.get("ACTION_WAVE_OFF_THR", "0.20"))
ACTION_WAVE_CONFIRM_FRAMES = int(os.environ.get("ACTION_WAVE_CONFIRM_FRAMES", "3"))
ACTION_WAVE_RELEASE_FRAMES = int(os.environ.get("ACTION_WAVE_RELEASE_FRAMES", "8"))

ACTION_PUNCH_ON_THR = float(os.environ.get("ACTION_PUNCH_ON_THR", "0.45"))
ACTION_PUNCH_OFF_THR = float(os.environ.get("ACTION_PUNCH_OFF_THR", "0.20"))
ACTION_PUNCH_CONFIRM_FRAMES = int(os.environ.get("ACTION_PUNCH_CONFIRM_FRAMES", "3"))
ACTION_PUNCH_RELEASE_FRAMES = int(os.environ.get("ACTION_PUNCH_RELEASE_FRAMES", "8"))
ACTION_FIGHT_DISTANCE_RATIO = float(os.environ.get("ACTION_FIGHT_DISTANCE_RATIO", "1.40"))
ACTION_FIGHT_CONFIRM_FRAMES = int(os.environ.get("ACTION_FIGHT_CONFIRM_FRAMES", "4"))
ACTION_FIGHT_RELEASE_FRAMES = int(os.environ.get("ACTION_FIGHT_RELEASE_FRAMES", "12"))

