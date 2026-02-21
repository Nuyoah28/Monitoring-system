from queue import Queue
from config import DevConfig as Config
cacheQueue = Queue()
cacheMax = 250
STREAM_RAW_URL = Config.STREAM_URL+'/live/raw' # python后端拉原始流的地址
STREAM_PROCESSED_URL = Config.STREAM_URL+'/live/ai' # python后端推处理之后的流的地址

# -----------------------------------------------------------------------
# TYPE_LIST: 检测能力开关列表
# 顺序严格对应数据库 case_type_info 表 (caseType 1~12)
# 由 Java 后端通过 /api/v1/monitor-device/type 接口下发
#
#   索引  caseType  含义              当前检测方式
#   [0]     1      进入危险区域       姿态估计(禁区检测)
#   [1]     2      烟雾              Mamba-YOLO (class_id=1, smoke)
#   [2]     3      区域停留          暂未实现
#   [3]     4      摔倒              姿态估计(跌倒检测)
#   [4]     5      明火              Mamba-YOLO (class_id=0, fire)
#   [5]     6      吸烟              Mamba-YOLO (class_id=1, smoke) — 与烟雾共用
#   [6]     7      打架              姿态估计(挥拳检测)
#   [7]     8      垃圾乱放          Mamba-YOLO (需添加 extra_prompt)
#   [8]     9      冰面              Mamba-YOLO (需添加 extra_prompt)
#   [9]    10      电动车进楼         Mamba-YOLO (需添加 extra_prompt)
#  [10]    11      载具占用车道       Mamba-YOLO (需添加 extra_prompt)
#  [11]    12      挥手呼救          姿态估计(挥手检测)
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
preList = [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]
avg_hip_y_pre, v_y, indices1, left_angle_pre, right_angle_pre, right_hand_pre, s, left_hand_pre, left_angle_vari, right_angle_vari, cond1, cond2, cond3, cond7, cond4, cond5, cond6, cond8, left_hand_pos_x, right_hand_pos_x, cond_right_hand, cond_left_hand, cond_left_hand_y, cond_right_hand_y, indices2, indices3, union1, indices_hand, indices_danger, fire_indices, smoke_indices, indices4, indices5 = None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None
