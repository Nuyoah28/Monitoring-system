from __future__ import annotations

import re
from typing import Optional

from agent_core.constants import (
    CASE_TYPE_ALIASES,
    DETECTION_ACTION_KEYWORDS,
    DETECTION_TARGET_KEYWORDS,
    HIGH_LEVEL_KEYWORDS,
    LOW_LEVEL_KEYWORDS,
    STATUS_DONE_KEYWORDS,
    STATUS_PENDING_KEYWORDS,
    WARNING_LEVEL_KEYWORDS,
)
from agent_core.utils import contains_any, normalize_text, safe_int, unique_preserve_order


def extract_case_types(question: str) -> list[int]:
    normalized = normalize_text(question)
    matched: list[str] = []
    for case_type, aliases in CASE_TYPE_ALIASES.items():
        if any(normalize_text(alias) in normalized for alias in aliases):
            matched.append(str(case_type))
    return [int(item) for item in unique_preserve_order(matched)]


def extract_warning_levels(question: str) -> list[int]:
    normalized = (question or "").replace(" ", "").lower()
    matched: list[str] = []
    for level, keywords in WARNING_LEVEL_KEYWORDS.items():
        if contains_any(normalized, keywords):
            matched.append(str(level))
    if not matched and contains_any(normalized, HIGH_LEVEL_KEYWORDS):
        matched.extend(["4", "5"])
    if not matched and contains_any(normalized, LOW_LEVEL_KEYWORDS):
        matched.extend(["1", "2"])
    return [int(item) for item in unique_preserve_order(matched)]


def extract_status(question: str) -> Optional[int]:
    if contains_any(question, STATUS_PENDING_KEYWORDS):
        return 0
    if contains_any(question, STATUS_DONE_KEYWORDS):
        return 1
    return None


def extract_processing_content(question: str) -> Optional[str]:
    match = re.search(r"(?:处理说明|处理内容|备注)\s*[:：]?\s*(.+)$", question)
    if match:
        return match.group(1).strip()
    return None


def extract_alarm_id(question: str) -> Optional[int]:
    patterns = [
        r"(?:告警|报警|警报|事件)\s*(?:id|ID|编号)?\s*[:：]?\s*(\d+)",
        r"(?:id|ID)\s*[:：]?\s*(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, question)
        if match:
            return safe_int(match.group(1))
    return None


def extract_monitor_id(question: str) -> Optional[int]:
    patterns = [
        r"(?:监控点|摄像头|监控|点位)\s*(?:id|ID|编号)?\s*[:：]?\s*(\d+)",
        r"(\d+)\s*号?(?:监控点|摄像头|监控)",
    ]
    for pattern in patterns:
        match = re.search(pattern, question)
        if match:
            return safe_int(match.group(1))
    return None


def extract_detection_prompts(question: str) -> list[str]:
    if not contains_any(question, DETECTION_ACTION_KEYWORDS):
        return []
    if not contains_any(question, DETECTION_TARGET_KEYWORDS):
        return []

    candidate = question
    for prefix in DETECTION_ACTION_KEYWORDS:
        if prefix in candidate:
            candidate = candidate.split(prefix, 1)[1]
            break

    candidate = re.sub(r"^(目标|内容|提示词|prompt|帮我|我想|为我)\s*", "", candidate)
    candidate = candidate.replace("：", ":").split(":", 1)[-1]
    candidate = re.sub(r"[。？！]$", "", candidate)
    candidate = (
        candidate.replace("，", ",")
        .replace("、", ",")
        .replace("；", ",")
        .replace(";", ",")
    )
    items: list[str] = []
    for part in candidate.split(","):
        cleaned = re.sub(r"^(目标|物体|对象|内容)\s*", "", part.strip())
        cleaned = re.sub(r"(可以吗|行吗|吧)$", "", cleaned).strip()
        if cleaned:
            items.append(cleaned)
    return unique_preserve_order(items)


def extract_alarm_update(question: str) -> Optional[dict]:
    alarm_id = extract_alarm_id(question)
    if alarm_id is None:
        return None

    if not contains_any(question, ["标记", "更新", "改成", "改为", "设为", "处理完成", "重新打开"]):
        return None

    status = extract_status(question)
    if status is None and contains_any(question, ["改为未处理", "标记为未处理", "重新打开", "恢复未处理"]):
        status = 0
    if status is None:
        return None

    return {
        "alarm_id": alarm_id,
        "status": status,
        "processing_content": extract_processing_content(question),
    }
