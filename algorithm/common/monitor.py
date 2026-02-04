from queue import Queue
from config import DevConfig as Config
cacheQueue = Queue()
cacheMax = 250
STREAM_RAW_URL = Config.STREAM_URL+'/live/raw' # python后端拉原始流的地址
STREAM_PROCESSED_URL = Config.STREAM_URL+'/live/ai' # python后端推处理之后的流的地址
# 0 火，1 抽烟，2 跌倒，3 挥拳，4挥手，5 危险区域
TYPE_LIST = [True, False, True, True, True, False]
#TYPE_LIST = [False, True, False, False, False, True]
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
