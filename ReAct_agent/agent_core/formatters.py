from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence

from agent_core.constants import CASE_TYPE_NAMES
from agent_core.utils import parse_alarm_display_time


def describe_case_types(case_types: Optional[Sequence[int]]) -> str:
    if not case_types:
        return "全部类型"
    return "、".join(CASE_TYPE_NAMES.get(case_type, f"类型{case_type}") for case_type in case_types)


def describe_warning_levels(levels: Optional[Sequence[int]]) -> str:
    if not levels:
        return "全部等级"
    return "、".join(f"{level}级" for level in levels)


def format_time_range(start_time: Optional[str], end_time: Optional[str]) -> str:
    if start_time and end_time:
        return f"{start_time} 至 {end_time}"
    if start_time:
        return f"{start_time} 之后"
    if end_time:
        return f"{end_time} 之前"
    return "全部时间"


def monitor_abilities(monitor: dict) -> list[str]:
    abilities: list[str] = []
    for item in monitor.get("ability") or []:
        if item.get("checked"):
            abilities.append(str(item.get("name")))
    return abilities


def describe_alarm_filters(
    *,
    case_types: Optional[Sequence[int]] = None,
    status: Optional[int] = None,
    warning_levels: Optional[Sequence[int]] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> str:
    parts = [f"类型：{describe_case_types(case_types)}"]
    if status is None:
        parts.append("状态：全部")
    else:
        parts.append("状态：已处理" if status == 1 else "状态：未处理")
    parts.append(f"等级：{describe_warning_levels(warning_levels)}")
    parts.append(f"时间：{format_time_range(start_time, end_time)}")
    return "；".join(parts)


def format_alarm_items(
    alarms: Sequence[dict],
    *,
    title: str,
    total_count: Optional[int] = None,
) -> str:
    if not alarms:
        return f"{title}：暂无符合条件的告警。"

    total = total_count if total_count is not None else len(alarms)
    lines = [f"{title}：共 {total} 条。", ""]
    for index, alarm in enumerate(alarms[:10], start=1):
        lines.append(
            f"{index}. ID {alarm.get('id', '-')}"
            f" | 事件 {alarm.get('eventName', '未知')}"
            f" | 监控点 {alarm.get('name', '未知')}"
            f" | 区域 {alarm.get('department', '未知')}"
            f" | 等级 {alarm.get('level', '未知')}"
            f" | 状态 {alarm.get('deal', '未知')}"
            f" | 时间 {alarm.get('date', '未知')}"
        )
        if alarm.get("content"):
            lines.append(f"   处置说明：{alarm.get('content')}")
    if total > 10:
        lines.append(f"... 其余 {total - 10} 条未展开。")
    return "\n".join(lines)


def format_alarm_count(
    count: int,
    *,
    case_types: Optional[Sequence[int]] = None,
    status: Optional[int] = None,
    warning_levels: Optional[Sequence[int]] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> str:
    filters = describe_alarm_filters(
        case_types=case_types,
        status=status,
        warning_levels=warning_levels,
        start_time=start_time,
        end_time=end_time,
    )
    return f"告警数量统计：{count} 条。\n筛选条件：{filters}"


def format_alarm_history(history_data: Optional[dict], defer: int) -> str:
    if not history_data:
        return "暂无告警趋势数据。"

    label = {1: "今天", 3: "近3天", 7: "近7天", 30: "近30天"}.get(defer, f"近{defer}天")
    lines = [f"告警趋势概览（{label}）：", ""]
    for title, key in [("总量趋势", "graph1"), ("区域分布", "graph2"), ("类型分布", "graph3")]:
        graph = history_data.get(key) or []
        if not graph:
            continue
        lines.append(f"{title}：")
        for item in graph[:12]:
            lines.append(f"- {item.get('period', '未知')}: {item.get('cnt', 0)}")
        lines.append("")
    return "\n".join(lines).strip()


def format_realtime_data(realtime_data: Optional[dict]) -> str:
    if not realtime_data:
        return "暂无实时告警数据。"

    total = realtime_data.get("alarmTotal") or {}
    lines = [
        "实时告警概况：",
        f"- 总告警数：{total.get('total', 0)}",
        f"- 今日新增：{total.get('todayNew', 0)}",
        f"- 较昨日变化：{total.get('dayChange', 0)}",
        "",
    ]
    case_type_list = realtime_data.get("alarmCaseTypeTotalList") or []
    if case_type_list:
        lines.append("按类型统计：")
        for item in case_type_list:
            lines.append(
                f"- {item.get('caseTypeName', '未知')}: "
                f"今日 {item.get('todayNew', 0)} 条，累计 {item.get('total', 0)} 条"
            )
    return "\n".join(lines)


def format_weather_data(monitor: Optional[dict], data, *, single: bool) -> str:
    monitor_label = monitor.get("name") if monitor else "该监控点"
    if not data:
        return f"{monitor_label}暂无天气数据。"

    if single:
        return (
            f"{monitor_label}最新天气："
            f"温度 {data.get('temperature', '未知')}℃，"
            f"湿度 {data.get('humidity', '未知')}%，"
            f"天气 {data.get('weather', '未知')}，"
            f"时间 {data.get('createTime', '未知')}。"
        )

    lines = [f"{monitor_label}历史天气记录：共 {len(data)} 条。", ""]
    for index, item in enumerate(data[:10], start=1):
        lines.append(
            f"{index}. 温度 {item.get('temperature', '未知')}℃"
            f" | 湿度 {item.get('humidity', '未知')}%"
            f" | 天气 {item.get('weather', '未知')}"
            f" | 时间 {item.get('createTime', '未知')}"
        )
    if len(data) > 10:
        lines.append(f"... 其余 {len(data) - 10} 条未展开。")
    return "\n".join(lines)


def format_monitor_list(monitor_list: Sequence[dict]) -> str:
    if not monitor_list:
        return "暂无监控点数据。"

    lines = [f"监控点列表：共 {len(monitor_list)} 个。", ""]
    for index, monitor in enumerate(monitor_list[:10], start=1):
        lines.append(
            f"{index}. {monitor.get('name', '未知')} (ID {monitor.get('id', '-')})"
            f" | 区域 {monitor.get('department', '未知')}"
            f" | 负责人 {monitor.get('leader', '未知')}"
            f" | 状态 {'运行中' if monitor.get('running') else '已停止'}"
            f" | 告警次数 {monitor.get('alarmCnt', 0)}"
        )
        abilities = monitor_abilities(monitor)
        if abilities:
            lines.append(f"   已开能力：{'、'.join(abilities)}")
    if len(monitor_list) > 10:
        lines.append(f"... 其余 {len(monitor_list) - 10} 个未展开。")
    return "\n".join(lines)


def format_monitor_detail(monitor: Optional[dict]) -> str:
    if not monitor:
        return "未找到对应的监控点。"
    lines = [
        f"监控点详情：{monitor.get('name', '未知')}",
        f"- ID：{monitor.get('id', '-')}",
        f"- 区域：{monitor.get('department', '未知')}",
        f"- 负责人：{monitor.get('leader', '未知')}",
        f"- 状态：{'运行中' if monitor.get('running') else '已停止'}",
        f"- 告警次数：{monitor.get('alarmCnt', 0)}",
        f"- 视频流：{monitor.get('video', '暂无')}",
    ]
    abilities = monitor_abilities(monitor)
    if abilities:
        lines.append(f"- 已开能力：{'、'.join(abilities)}")
    return "\n".join(lines)


def sort_alarms_by_time(alarms: list[dict]) -> list[dict]:
    return sorted(
        alarms,
        key=lambda item: parse_alarm_display_time(item.get("date")) or datetime.min,
        reverse=True,
    )
