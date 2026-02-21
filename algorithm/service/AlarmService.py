import requests
from util.Logger import setup_logger
from flask import current_app as app, jsonify
import uuid
from common import monitor as monitorCommon
import copy
import time
import threading
from util import UploadCos
from config import DevConfig as Config

logger = setup_logger()

# -----------------------------------------------------------------------
# warningList 索引 → Java 后端 caseType 的映射
# 顺序严格对应 TYPE_LIST 和数据库 case_type_info 表
#
#   warningList[i]    caseType    含义
#   [0]                 1        进入危险区域
#   [1]                 2        烟雾
#   [2]                 3        区域停留
#   [3]                 4        摔倒
#   [4]                 5        明火
#   [5]                 6        吸烟
#   [6]                 7        打架
#   [7]                 8        垃圾乱放
#   [8]                 9        冰面
#   [9]                10        电动车进楼
#   [10]               11        载具占用车道
#   [11]               12        挥手呼救
#
# 现在是 1:1 映射: caseType = warningList索引 + 1
# -----------------------------------------------------------------------


def postAlarm(warningList):
    indices = [index for index, value in enumerate(warningList) if value]
    logger.info("warningList: " + str(indices))
    clipId = str(uuid.uuid4())
    for index, element in enumerate(warningList):
        if element:
            # warningList 的索引直接对应 caseType - 1
            # 例如: warningList[0]=True → caseType=1 (进入危险区域)
            #       warningList[4]=True → caseType=5 (明火)
            caseType = index + 1

            param = Config.BACKEND_URL + "/api/v1/alarm/receive?clipId=" + clipId + "&caseType=" + str(
                caseType) + "&cameraId=1"
            print(param)
            try:
                requests.post(param).json()
                print("post alarm success")
            except Exception as e:
                logger.error("post alarm failed: " + str(e))

    # 上传视频片段
    print(clipId)
    stream_thread = threading.Thread(target=uploadClip, name="upload_thread-" + clipId, args=(clipId,))
    stream_thread.start()


def uploadClip(uuidParam):
    snapshot = list(monitorCommon.cacheQueue.queue)
    cacheQueue = [copy.deepcopy(item) for item in snapshot]
    time.sleep(10)
    snapshot = list(monitorCommon.cacheQueue.queue)
    addedQueue = [copy.deepcopy(item) for item in snapshot]
    cacheQueue.extend(addedQueue)
    UploadCos.upload2Cos(cacheQueue, uuidParam)
    return True
