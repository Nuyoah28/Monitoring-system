import copy
import os
import threading
import time
import uuid
from datetime import datetime
from urllib.parse import urlencode

import requests

from common import monitor as monitorCommon
from config import RuntimeConfig as Config
from service import AlarmCacheService
from util import UploadCos
from util.Logger import setup_logger

logger = setup_logger()


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
    if not clip_path or not os.path.exists(clip_path):
        raise RuntimeError(f"alarm clip not ready: {item['clip_id']}")
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
    if not indices:
        return

    logger.info("warningList: %s", indices)
    clipId = str(uuid.uuid4())
    cameraId = Config.MONITOR_ID
    occurredAt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    snapshot = list(monitorCommon.cacheQueue.queue)
    cacheQueue = [copy.deepcopy(item) for item in snapshot]

    def _prepare_clip_and_post():
        try:
            clipPath = uploadClip(clipId, cacheQueue)
        except Exception as e:
            logger.error("prepare alarm clip failed: %s", e)
            return

        for index, element in enumerate(warningList):
            if element:
                caseType = index + 1
                AlarmCacheService.enqueue_alarm(clipId, cameraId, caseType, clipPath, occurredAt)

        print(clipId)
        for index, element in enumerate(warningList):
            if not element:
                continue
            caseType = index + 1
            try:
                _post_alarm_to_backend(clipId, cameraId, caseType, occurredAt)
                AlarmCacheService.mark_synced(clipId, cameraId, caseType)
                print("post alarm success")
            except Exception as e:
                AlarmCacheService.mark_failed(clipId, cameraId, caseType, e)
                logger.error("post alarm failed: %s", e)

    stream_thread = threading.Thread(target=_prepare_clip_and_post, name="upload_thread-" + clipId)
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
    if not clipPath:
        raise RuntimeError("alarm clip is empty")
    logger.info("alarm clip saved locally: %s", clipPath)
    UploadCos.uploadFile2Cos(clipPath, uuidParam)
    return clipPath
