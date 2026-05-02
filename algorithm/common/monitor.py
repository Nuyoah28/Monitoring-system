from queue import Queue
from config import RuntimeConfig as Config

cacheQueue = Queue()
cacheMax = 250

STREAM_RAW_URL = Config.STREAM_RAW_URL  # python后端拉原始流的地址
STREAM_PROCESSED_URL = Config.STREAM_PROCESSED_URL  # python后端推处理之后的流的地址

# 添加新的配置项用于视频流处理
VIDEO_PROCESSING_ENABLED = Config.VIDEO_PROCESSING_ENABLED
VIDEO_CACHE_SIZE = Config.VIDEO_CACHE_SIZE

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
TYPE_LIST = list(Config.TYPE_LIST)

# 左上 右下
AREA_LIST = list(Config.AREA_LIST)

capture_width = Config.CAPTURE_WIDTH
capture_height = Config.CAPTURE_HEIGHT
display_width = Config.DISPLAY_WIDTH
display_height = Config.DISPLAY_HEIGHT
framerate = Config.FRAMERATE
flip_method = Config.FLIP_METHOD
# ST-GCN++ maintains its own internal buffer, so preList only needs
# danger zone + Mamba-YOLO state (indices_danger, fire_indices, smoke_indices)
preList = [None, None, None]

# -----------------------------------------------------------------------
# Mamba-YOLO 自定义检测目标（在"火"和"烟"之外动态扩展）
# 这个列表会在 Flask 进程里修改，在 video stream 进程里被读取。
# -----------------------------------------------------------------------
CUSTOM_DETECTION_PROMPTS = list(Config.CUSTOM_DETECTION_PROMPTS)

# 标志位：提示词是否发生更改
PROMPTS_CHANGED = False

ACTION_MODEL_BACKEND = Config.ACTION_MODEL_BACKEND
ACTION_CTR_GCN_ROOT = Config.ACTION_CTR_GCN_ROOT
ACTION_CTR_GCN_FUSION = Config.ACTION_CTR_GCN_FUSION
ACTION_CTR_GCN_FUSION_MODE = Config.ACTION_CTR_GCN_FUSION_MODE
ACTION_CTR_GCN_JOINT_WEIGHTS = Config.ACTION_CTR_GCN_JOINT_WEIGHTS
ACTION_CTR_GCN_BONE_WEIGHTS = Config.ACTION_CTR_GCN_BONE_WEIGHTS
ACTION_CTR_GCN_WEIGHTS = Config.ACTION_CTR_GCN_WEIGHTS
ACTION_CTR_GCN_JOINT_ALPHA = Config.ACTION_CTR_GCN_JOINT_ALPHA
ACTION_CTR_GCN_BONE_ALPHA = Config.ACTION_CTR_GCN_BONE_ALPHA
ACTION_LABEL_ORDER = Config.ACTION_LABEL_ORDER
ACTION_WINDOW_SIZE = Config.ACTION_WINDOW_SIZE
ACTION_MIN_FRAMES = Config.ACTION_MIN_FRAMES
ACTION_SMOOTH = Config.ACTION_SMOOTH
ACTION_MAX_TRACKS = Config.ACTION_MAX_TRACKS
ACTION_TOP_K_TRACKS = Config.ACTION_TOP_K_TRACKS
ACTION_INFER_INTERVAL = Config.ACTION_INFER_INTERVAL
ACTION_MAX_MISSING = Config.ACTION_MAX_MISSING

ACTION_FALL_ON_THR = Config.ACTION_FALL_ON_THR
ACTION_FALL_OFF_THR = Config.ACTION_FALL_OFF_THR
ACTION_FALL_HOLD_FRAMES = Config.ACTION_FALL_HOLD_FRAMES
ACTION_FALL_RELEASE_FRAMES = Config.ACTION_FALL_RELEASE_FRAMES
ACTION_FALL_LATCH = Config.ACTION_FALL_LATCH

ACTION_WAVE_ON_THR = Config.ACTION_WAVE_ON_THR
ACTION_WAVE_OFF_THR = Config.ACTION_WAVE_OFF_THR
ACTION_WAVE_CONFIRM_FRAMES = Config.ACTION_WAVE_CONFIRM_FRAMES
ACTION_WAVE_RELEASE_FRAMES = Config.ACTION_WAVE_RELEASE_FRAMES

ACTION_PUNCH_ON_THR = Config.ACTION_PUNCH_ON_THR
ACTION_PUNCH_OFF_THR = Config.ACTION_PUNCH_OFF_THR
ACTION_PUNCH_CONFIRM_FRAMES = Config.ACTION_PUNCH_CONFIRM_FRAMES
ACTION_PUNCH_RELEASE_FRAMES = Config.ACTION_PUNCH_RELEASE_FRAMES
ACTION_FIGHT_DISTANCE_RATIO = Config.ACTION_FIGHT_DISTANCE_RATIO
ACTION_FIGHT_CONFIRM_FRAMES = Config.ACTION_FIGHT_CONFIRM_FRAMES
ACTION_FIGHT_RELEASE_FRAMES = Config.ACTION_FIGHT_RELEASE_FRAMES

WARNING_STREAK_MIN_HITS = Config.WARNING_STREAK_MIN_HITS

