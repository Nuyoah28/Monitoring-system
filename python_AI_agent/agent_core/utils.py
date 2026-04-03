from __future__ import annotations

import copy
import hashlib
import re
from datetime import datetime, timedelta
from typing import Any, Optional, Sequence

from agent_core.constants import NON_RETRYABLE_SPARK_MARKERS


def contains_any(text: str, keywords: Sequence[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def normalize_text(text: str) -> str:
    return re.sub(
        r"[\s`~!@#$%^&*()\-_=+\[\]{}\\|;:'\",.<>/?，。！？、；：“”‘’（）【】《》]+",
        "",
        (text or "").lower(),
    )


def unique_preserve_order(items: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    try:
        if value in (None, ""):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def is_non_retryable_spark_error(error: Exception | str) -> bool:
    message = str(error).lower()
    return any(marker in message for marker in NON_RETRYABLE_SPARK_MARKERS)


def build_conversation_key(user_token: Optional[str], fallback: str = "anonymous:default") -> str:
    if user_token:
        digest = hashlib.sha1(user_token.encode("utf-8")).hexdigest()[:12]
        return f"user:{digest}"
    return fallback


def parse_date_string(date_str: str) -> Optional[datetime]:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日", "%Y年%m月%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def build_day_range(dt: datetime) -> tuple[str, str]:
    return (
        dt.strftime("%Y-%m-%d 00:00:00"),
        dt.strftime("%Y-%m-%d 23:59:59"),
    )


def extract_absolute_dates(question: str) -> list[datetime]:
    matches = re.findall(r"(20\d{2}[/-年]\d{1,2}[/-月]\d{1,2}(?:日)?)", question or "")
    parsed: list[datetime] = []
    for raw in matches:
        normalized = raw.replace("年", "-").replace("月", "-").replace("日", "").replace("/", "-")
        dt = parse_date_string(normalized)
        if dt:
            parsed.append(dt)
    return parsed


def extract_time_range(question: str) -> tuple[Optional[str], Optional[str]]:
    now = datetime.now()
    parsed_dates = extract_absolute_dates(question)
    if len(parsed_dates) >= 2:
        start, end = parsed_dates[0], parsed_dates[1]
        if start > end:
            start, end = end, start
        return build_day_range(start)[0], build_day_range(end)[1]
    if len(parsed_dates) == 1:
        return build_day_range(parsed_dates[0])

    normalized = (question or "").replace(" ", "")
    if "今天" in normalized or "今日" in normalized:
        return build_day_range(now)
    if "昨天" in normalized:
        return build_day_range(now - timedelta(days=1))
    if contains_any(normalized, ["近3天", "最近3天", "三天内"]):
        start = now - timedelta(days=2)
        return build_day_range(start)[0], build_day_range(now)[1]
    if contains_any(normalized, ["近7天", "最近7天", "最近一周", "一周内"]):
        start = now - timedelta(days=6)
        return build_day_range(start)[0], build_day_range(now)[1]
    if contains_any(normalized, ["近30天", "最近30天", "最近一个月", "一个月内"]):
        start = now - timedelta(days=29)
        return build_day_range(start)[0], build_day_range(now)[1]
    if "本周" in normalized:
        start = now - timedelta(days=now.weekday())
        return build_day_range(start)[0], build_day_range(now)[1]
    if "本月" in normalized:
        start = now.replace(day=1)
        return build_day_range(start)[0], build_day_range(now)[1]
    return None, None


def has_explicit_time_reference(question: str) -> bool:
    start, end = extract_time_range(question)
    return bool(start or end)


def extract_history_defer(question: str) -> int:
    normalized = (question or "").replace(" ", "")
    if contains_any(normalized, ["今天", "今日", "24小时", "一天"]):
        return 1
    if contains_any(normalized, ["近3天", "最近3天", "三天"]):
        return 3
    if contains_any(normalized, ["近30天", "最近30天", "最近一个月", "一个月"]):
        return 30
    return 7


def parse_alarm_display_time(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    current_year = datetime.now().year
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m-%d %H:%M", "%m-%d %I:%M"):
        try:
            parsed = datetime.strptime(value, fmt)
            if fmt.startswith("%m-"):
                return parsed.replace(year=current_year)
            return parsed
        except ValueError:
            continue
    return None


def in_time_range(display_time: Optional[str], start_time: Optional[str], end_time: Optional[str]) -> bool:
    if not start_time and not end_time:
        return True

    parsed = parse_alarm_display_time(display_time)
    if not parsed:
        return True

    start = None
    end = None
    if start_time:
        try:
            start = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            start = None
    if end_time:
        try:
            end = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            end = None

    if start and parsed < start:
        return False
    if end and parsed > end:
        return False
    return True


def shallow_copy_dict(value: Optional[dict[str, Any]]) -> dict[str, Any]:
    return copy.deepcopy(value or {})
