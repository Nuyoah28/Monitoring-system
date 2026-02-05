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


def postAlarm(warningList):
    indices = [index for index, value in enumerate(warningList) if value]
    logger.info("warningList: " + str(indices))
    clipId = str(uuid.uuid4())
    for index, element in enumerate(warningList):
        # 0 火，1 抽烟，2 跌倒，3 挥拳，4挥手，5 危险区域
        caseType = 0
        if index == 0:
            caseType = 4
        if index == 1:
            caseType = 5
        if index == 2:
            caseType = 3
        if index == 3:
            caseType = 6
        if index == 4:
            caseType = 2
        if index == 5:
            caseType = 1

        if element: #java后端
            param = Config.BACKEND_URL+"/api/v1/alarm/receive?clipId=" + clipId + "&caseType=" + str(
                caseType) + "&cameraId=1"
            print(param)
            requests.post(param).json()
            print("post alarm success")
    # todo: upload video clip to cos
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
