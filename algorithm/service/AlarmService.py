import requests
import os
from urllib.parse import urlencode
from util.Logger import setup_logger
from flask import current_app as app, jsonify
import uuid
from datetime import datetime
from common import monitor as monitorCommon
import copy
import time
import threading
from util import UploadCos
from config import DevConfig as Config
from service import AlarmCacheService

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


def _post_alarm_to_backend(clip_id, camera_id, case_type, occurred_at=None):
    query = {
        "clipId": clip_id,
        "caseType": case_type,
        "cameraId": camera_id,
    }
    if occurred_at:
        query["occurredAt"] = occurred_at
    param = Config.BACKEND_URL + "/api/v1/alarm/receive?" + urlencode(query)
    print(param)
    response = requests.post(param, timeout=getattr(Config, "ALARM_REQUEST_TIMEOUT_SECONDS", 5))
    response.raise_for_status()
    result = response.json()
    if result.get("code") != "00000":
        raise RuntimeError(result.get("message") or "backend receive alarm failed")
    return result


def _sync_cached_alarm(item):
    clip_path = item.get("clip_path")
    if clip_path and os.path.exists(clip_path):
        UploadCos.uploadFile2Cos(clip_path, item["clip_id"])
    _post_alarm_to_backend(
        item["clip_id"],
        item["camera_id"],
        item["case_type"],
        item.get("occurred_at"),
    )


def startAlarmCacheSyncWorker():
    AlarmCacheService.start_sync_worker(_sync_cached_alarm)


def postAlarm(warningList):
    indices = [index for index, value in enumerate(warningList) if value]
    logger.info("warningList: " + str(indices))
    clipId = str(uuid.uuid4())
    cameraId = app.config.get("MONITOR_ID", Config.MONITOR_ID)
    occurredAt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    snapshot = list(monitorCommon.cacheQueue.queue)
    cacheQueue = [copy.deepcopy(item) for item in snapshot]

    for index, element in enumerate(warningList):
        if element:
            # warningList 的索引直接对应 caseType - 1
            # 例如: warningList[0]=True → caseType=1 (进入危险区域)
            #       warningList[4]=True → caseType=5 (明火)
            caseType = index + 1
            AlarmCacheService.enqueue_alarm(clipId, cameraId, caseType, None, occurredAt)
            try:
                _post_alarm_to_backend(clipId, cameraId, caseType, occurredAt)
                AlarmCacheService.mark_synced(clipId, cameraId, caseType)
                print("post alarm success")
            except Exception as e:
                AlarmCacheService.mark_failed(clipId, cameraId, caseType, e)
                logger.error("post alarm failed: " + str(e))

    # 上传视频片段
    print(clipId)
    stream_thread = threading.Thread(target=uploadClip, name="upload_thread-" + clipId, args=(clipId, cacheQueue))
    stream_thread.start()


def uploadClip(uuidParam, cacheQueue=None):
    if cacheQueue is None:
        snapshot = list(monitorCommon.cacheQueue.queue)
        cacheQueue = [copy.deepcopy(item) for item in snapshot]
    time.sleep(10)
    snapshot = list(monitorCommon.cacheQueue.queue)
    addedQueue = [copy.deepcopy(item) for item in snapshot]
    cacheQueue.extend(addedQueue)
    clipPath = AlarmCacheService.save_clip_frames(cacheQueue, uuidParam)
    if clipPath:
        AlarmCacheService.update_clip_path(uuidParam, clipPath)
        logger.info("alarm clip saved locally: " + clipPath)
    try:
        UploadCos.upload2Cos(cacheQueue, uuidParam)
    except Exception as e:
        AlarmCacheService.mark_clip_failed(uuidParam, e)
        logger.error("upload alarm clip to COS failed: " + str(e))
    return True
