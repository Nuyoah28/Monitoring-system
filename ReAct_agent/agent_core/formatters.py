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
    for index, alarm in enumerate(alarms, start=1):
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
        for item in graph:
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
    for index, item in enumerate(data, start=1):
        lines.append(
            f"{index}. 温度 {item.get('temperature', '未知')}℃"
            f" | 湿度 {item.get('humidity', '未知')}%"
            f" | 天气 {item.get('weather', '未知')}"
            f" | 时间 {item.get('createTime', '未知')}"
        )
    return "\n".join(lines)


def format_monitor_list(monitor_list: Sequence[dict]) -> str:
    if not monitor_list:
        return "暂无监控点数据。"

    lines = [f"监控点列表：共 {len(monitor_list)} 个。", ""]
    for index, monitor in enumerate(monitor_list, start=1):
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


def _shorten(value: object, limit: int = 80) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def _sort_items_by_text_time(items: Sequence[dict], key: str) -> list[dict]:
    return sorted(items, key=lambda item: str(item.get(key) or ""), reverse=True)


def _format_number(value: object, suffix: str = "") -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "未知"
    if number.is_integer():
        return f"{int(number)}{suffix}"
    return f"{number:.1f}{suffix}"


def format_owner_profile(profile: Optional[dict]) -> str:
    if not profile:
        return "未查到当前业主的个人资料，请确认已登录业主端账号。"
    notify = "已开启" if profile.get("notifyEnabled") is not False else "已关闭"
    resident = "是" if profile.get("isResident") else "否"
    return "\n".join(
        [
            "当前业主个人资料：",
            f"- 用户ID：{profile.get('id', '-')}",
            f"- 用户名：{profile.get('name') or profile.get('userName') or '未填写'}",
            f"- 手机号：{profile.get('phone') or '未填写'}",
            f"- 常驻区域：{profile.get('homeArea') or '未填写'}",
            f"- 居民身份：{resident}",
            f"- 消息提醒：{notify}",
        ]
    )


def format_owner_messages(messages: Optional[Sequence[dict]], *, limit: int = 8) -> str:
    if not messages:
        return "当前没有查到社区提醒。"
    sorted_items = _sort_items_by_text_time(messages, "timestamp")
    selected = sorted_items[:limit]
    lines = [f"社区提醒：共 {len(messages)} 条，展示最近 {len(selected)} 条。", ""]
    for index, item in enumerate(selected, start=1):
        lines.append(
            f"{index}. {_shorten(item.get('message'), 120) or '未命名提醒'}"
            f" | 时间 {item.get('timestamp') or '未知'}"
        )
    return "\n".join(lines)


def format_owner_visitors(visitors: Optional[Sequence[dict]], *, limit: int = 8) -> str:
    if not visitors:
        return "当前没有查到访客登记记录。"
    sorted_items = _sort_items_by_text_time(visitors, "visitTime")
    selected = sorted_items[:limit]
    lines = [f"我的访客登记：共 {len(visitors)} 条，展示最近 {len(selected)} 条。", ""]
    for index, item in enumerate(selected, start=1):
        plate = item.get("plateNumber") or "未登记车牌"
        lines.append(
            f"{index}. {item.get('visitorName') or '未命名访客'}"
            f" | 到访时间 {item.get('visitTime') or '未知'}"
            f" | {plate}"
        )
    return "\n".join(lines)


def format_owner_repairs(repairs: Optional[Sequence[dict]], *, limit: int = 8) -> str:
    if not repairs:
        return "当前没有查到报修记录。"
    sorted_items = _sort_items_by_text_time(repairs, "reportTime")
    selected = sorted_items[:limit]
    lines = [f"我的报修记录：共 {len(repairs)} 条，展示最近 {len(selected)} 条。", ""]
    for index, item in enumerate(selected, start=1):
        lines.append(
            f"{index}. {item.get('deviceName') or '未填写设备'}"
            f" | 位置 {item.get('location') or '未填写'}"
            f" | 时间 {item.get('reportTime') or '未知'}"
        )
        if item.get("repairDetail"):
            lines.append(f"   详情：{_shorten(item.get('repairDetail'), 120)}")
    return "\n".join(lines)


def format_parking_realtime(data: Optional[dict]) -> str:
    if not data:
        return "暂无停车实时数据。"
    total = data.get("totalSpaces") or 0
    occupied = data.get("occupiedSpaces") or 0
    free = data.get("freeSpaces") or 0
    rate = data.get("occupancyRate")
    source = data.get("source") or "real"
    lines = [
        "停车实时状态：",
        f"- 数据源：{source}",
        f"- 总车位：{total}",
        f"- 已占用：{occupied}",
        f"- 空余车位：{free}",
        f"- 占用率：{rate if rate is not None else '未知'}%",
        f"- 更新时间：{data.get('updateTime') or '未知'}",
    ]
    zones = data.get("zones") or []
    if zones:
        lines.append("")
        lines.append("分区情况：")
        for zone in zones[:8]:
            zone_total = zone.get("totalSpaces") or 0
            zone_occupied = zone.get("occupiedSpaces") or 0
            lines.append(
                f"- {zone.get('areaName') or zone.get('areaCode') or '未知区域'}："
                f"{max(zone_total - zone_occupied, 0)} 空余 / {zone_total} 总数"
            )
    return "\n".join(lines)


def format_parking_traffic_summary(data: Optional[dict]) -> str:
    if not data:
        return "暂无车流量统计数据。"
    return "\n".join(
        [
            "停车场车流量统计：",
            f"- 数据源：{data.get('source') or 'real'}",
            f"- 今日进场：{data.get('todayInCount', 0)}",
            f"- 今日出场：{data.get('todayOutCount', 0)}",
            f"- 今日净流入：{data.get('todayNetFlow', 0)}",
            f"- 今日总流量：{data.get('todayTotalFlow', 0)}",
            f"- 最近进场：{data.get('latestInCount', 0)}",
            f"- 最近出场：{data.get('latestOutCount', 0)}",
            f"- 最近净流入：{data.get('latestNetFlow', 0)}",
            f"- 更新时间：{data.get('updateTime') or '未知'}",
        ]
    )


def format_environment_realtime(data: Optional[dict]) -> str:
    if not data:
        return "暂无实时环境数据。"
    return "\n".join(
        [
            "社区实时环境：",
            f"- 监控点ID：{data.get('monitorId') or '-'}",
            f"- 温度：{_format_number(data.get('temperature'), '℃')}",
            f"- 湿度：{_format_number(data.get('humidity'), '%')}",
            f"- PM2.5：{_format_number(data.get('pm25'))}",
            f"- 可燃气体：{_format_number(data.get('combustibleGas'), ' ppm')}",
            f"- AQI：{data.get('aqi') if data.get('aqi') is not None else '未知'}",
            f"- 更新时间：{data.get('createTime') or '未知'}",
        ]
    )


def format_environment_trend(data: Optional[Sequence[dict]], *, range_name: str = "day") -> str:
    if not data:
        return "暂无环境趋势数据。"
    label = {"day": "今日", "week": "本周", "month": "本月"}.get(range_name, range_name)
    selected = list(data)[-8:]
    lines = [f"社区环境趋势（{label}）：共 {len(data)} 个点，展示最近 {len(selected)} 个。", ""]
    for item in selected:
        lines.append(
            f"- {item.get('label') or item.get('time') or item.get('createTime') or '未知时间'}："
            f"湿度 {_format_number(item.get('humidity'), '%')}，"
            f"PM2.5 {_format_number(item.get('pm25'))}，"
            f"可燃气体 {_format_number(item.get('combustibleGas'), ' ppm')}，"
            f"AQI {item.get('aqi') if item.get('aqi') is not None else '未知'}"
        )
    return "\n".join(lines)
