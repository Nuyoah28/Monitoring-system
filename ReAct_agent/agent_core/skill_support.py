from __future__ import annotations

# AI辅助生成：本文件中的上下文事实记忆、监控点追溯补全与结构化观察逻辑由 GPT-5 Codex 协助完成，2026-04-04。

from typing import Any, Optional, Sequence

from agent_core import formatters
from agent_core.config.settings import AgentSettings
from agent_core.core.context import RequestContext
from agent_core.intent_utils import extract_alarm_id
from agent_core.memory.store import ConversationMemoryStore
from agent_core.utils import extract_time_range, in_time_range, normalize_text, safe_int


class SkillSupport:
    def __init__(self, backend: Any, memory_store: ConversationMemoryStore, settings: AgentSettings):
        self.backend = backend
        self.memory_store = memory_store
        self.settings = settings

    def get_conversation_state(self, conversation_key: str) -> dict[str, Any]:
        return self.memory_store.get_state(conversation_key)

    def remember_tool_state(
        self,
        request_context: RequestContext,
        tool_name: str,
        params: dict[str, Any],
        *,
        alarm_ids: Optional[Sequence[Optional[int]]] = None,
        monitor: Optional[dict[str, Any]] = None,
    ) -> None:
        updates: dict[str, Any] = {
            "last_tool_name": tool_name,
            "last_tool_params": dict(params),
        }

        if alarm_ids is not None:
            updates["last_alarm_ids"] = [
                alarm_id
                for alarm_id in (safe_int(item) for item in alarm_ids)
                if alarm_id is not None
            ]

        if monitor:
            monitor_id = safe_int(monitor.get("id"))
            if monitor_id is not None:
                updates["last_monitor_id"] = monitor_id
            monitor_name = monitor.get("name")
            if monitor_name:
                updates["last_monitor_name"] = monitor_name

        self.memory_store.update_state(request_context.conversation_key, **updates)

    def resolve_contextual_alarm_id(self, question: str, request_context: RequestContext) -> Optional[int]:
        alarm_id = extract_alarm_id(question)
        if alarm_id is not None:
            return alarm_id

        context_markers = [
            "刚才那个",
            "刚刚那个",
            "上一个告警",
            "上个告警",
            "上一条告警",
            "这个告警",
            "那个告警",
            "刚才那条",
            "上一个",
        ]
        if not any(marker in question for marker in context_markers):
            return None

        state = self.get_conversation_state(request_context.conversation_key)
        alarm_ids = state.get("last_alarm_ids") or []
        if isinstance(alarm_ids, list) and alarm_ids:
            return safe_int(alarm_ids[0])
        return None

    def resolve_monitor(
        self,
        request_context: RequestContext,
        *,
        question: str = "",
        monitor_id: Optional[int] = None,
        monitor_name: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        monitor_list = request_context.get_monitor_list(self.backend)
        if not monitor_list:
            return None

        if monitor_id is not None:
            for monitor in monitor_list:
                if safe_int(monitor.get("id")) == monitor_id:
                    return monitor

        lookup_text = (monitor_name or question or "").strip()
        if not lookup_text:
            return None

        normalized_lookup = normalize_text(lookup_text)
        best_monitor = None
        best_score = -1
        for monitor in monitor_list:
            score = 0
            for raw_value, weight in [
                (monitor.get("name"), 100),
                (monitor.get("department"), 70),
                (monitor.get("number"), 40),
            ]:
                if raw_value is None:
                    continue
                candidate = normalize_text(str(raw_value))
                if not candidate:
                    continue
                if candidate == normalized_lookup:
                    score = max(score, weight + len(candidate) * 2)
                elif candidate in normalized_lookup:
                    score = max(score, weight + len(candidate))
            if score > best_score:
                best_score = score
                best_monitor = monitor

        if best_score <= 0:
            return None
        return best_monitor

    def extract_time_window(self, params: dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
        time_range = params.get("time_range")
        if isinstance(time_range, dict):
            start_time = str(time_range.get("start") or "").strip() or None
            end_time = str(time_range.get("end") or "").strip() or None
            if start_time or end_time:
                return start_time, end_time

        time_text = str(params.get("time_text") or "").strip()
        if not time_text:
            return None, None
        return extract_time_range(time_text, now=request_context.current_time)

    def _normalize_int_list(self, value: Any) -> list[int]:
        if value is None:
            return []
        if not isinstance(value, list):
            value = [value]
        result: list[int] = []
        for item in value:
            parsed = safe_int(item)
            if parsed is not None:
                result.append(parsed)
        return result

    def fetch_alarm_pages(
        self,
        request_context: RequestContext,
        *,
        case_type: Optional[int] = None,
        status: Optional[int] = None,
        warning_level: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        alarms: list[dict[str, Any]] = []
        seen_ids: set[Any] = set()
        for page_num in range(1, self.settings.max_alarm_fetch_pages + 1):
            page = self.backend.get_alarm_list(
                page_num=page_num,
                page_size=self.settings.alarm_page_size,
                case_type=case_type,
                status=status,
                warning_level=warning_level,
                user_token=request_context.user_token,
            )
            if not page:
                break

            items = page.get("alarmList") or []
            if not items:
                break

            fresh_count = 0
            for item in items:
                alarm_id = item.get("id")
                if alarm_id in seen_ids:
                    continue
                seen_ids.add(alarm_id)
                alarms.append(item)
                fresh_count += 1

            if len(items) < self.settings.alarm_page_size or fresh_count == 0:
                break

        return alarms

    def query_alarm_union(
        self,
        request_context: RequestContext,
        *,
        case_types: Optional[Sequence[int]] = None,
        status: Optional[int] = None,
        warning_levels: Optional[Sequence[int]] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        case_type_list = list(case_types) if case_types else [None]
        warning_level_list = list(warning_levels) if warning_levels else [None]
        combined: list[dict[str, Any]] = []
        seen_ids: set[Any] = set()

        for case_type in case_type_list:
            for warning_level in warning_level_list:
                alarms = self.fetch_alarm_pages(
                    request_context,
                    case_type=case_type,
                    status=status,
                    warning_level=warning_level,
                )
                for alarm in alarms:
                    alarm_id = alarm.get("id")
                    if alarm_id in seen_ids:
                        continue
                    if not in_time_range(alarm.get("date"), start_time, end_time):
                        continue
                    seen_ids.add(alarm_id)
                    combined.append(alarm)
        return formatters.sort_alarms_by_time(combined)

    def handle_get_alarm_list(self, request_context: RequestContext, params: dict[str, Any]) -> str:
        case_types = self._normalize_int_list(params.get("case_types"))
        warning_levels = self._normalize_int_list(params.get("warning_levels"))
        status = safe_int(params.get("status"))
        start_time, end_time = self.extract_time_window(params)

        alarms = self.query_alarm_union(
            request_context,
            case_types=case_types or None,
            status=status,
            warning_levels=warning_levels or None,
            start_time=start_time,
            end_time=end_time,
        )

        requested_page_size = safe_int(params.get("page_size"))
        page_size = requested_page_size if requested_page_size and requested_page_size > 0 else len(alarms)
        selected_alarms = alarms[:page_size] if page_size else alarms

        self.remember_tool_state(
            request_context,
            "get_alarm_list",
            params,
            alarm_ids=[alarm.get("id") for alarm in selected_alarms],
        )
        return formatters.format_alarm_items(
            selected_alarms,
            title="告警列表",
            total_count=len(alarms),
        )

    def handle_get_alarm_count(self, request_context: RequestContext, params: dict[str, Any]) -> str:
        case_types = self._normalize_int_list(params.get("case_types"))
        warning_levels = self._normalize_int_list(params.get("warning_levels"))
        status = safe_int(params.get("status"))
        start_time, end_time = self.extract_time_window(params)

        alarms = self.query_alarm_union(
            request_context,
            case_types=case_types or None,
            status=status,
            warning_levels=warning_levels or None,
            start_time=start_time,
            end_time=end_time,
        )
        self.remember_tool_state(
            request_context,
            "get_alarm_count",
            params,
            alarm_ids=[alarm.get("id") for alarm in alarms[:10]],
        )
        return formatters.format_alarm_count(
            len(alarms),
            case_types=case_types or None,
            status=status,
            warning_levels=warning_levels or None,
            start_time=start_time,
            end_time=end_time,
        )

    def handle_get_alarm_history(self, request_context: RequestContext, params: dict[str, Any]) -> str:
        defer = safe_int(params.get("defer"), 7) or 7
        history = self.backend.get_alarm_history(defer=defer)
        self.remember_tool_state(request_context, "get_alarm_history", params)
        return formatters.format_alarm_history(history, defer)

    def handle_get_realtime_alarm(self, request_context: RequestContext, params: dict[str, Any]) -> str:
        del request_context, params
        realtime = self.backend.get_realtime_alarm()
        return formatters.format_realtime_data(realtime)

    def handle_get_alarm_detail(self, request_context: RequestContext, params: dict[str, Any]) -> str:
        alarm_id = safe_int(params.get("alarm_id"))
        if alarm_id is None:
            return "缺少告警 ID。"
        alarm = self.backend.get_alarm_by_id(alarm_id)
        if not alarm:
            return f"未找到 ID 为 {alarm_id} 的告警。"
        self.remember_tool_state(
            request_context,
            "get_alarm_detail",
            params,
            alarm_ids=[alarm_id],
        )
        return formatters.format_alarm_items([alarm], title="告警详情", total_count=1)

    def handle_update_alarm_status(self, request_context: RequestContext, params: dict[str, Any]) -> str:
        alarm_id = safe_int(params.get("alarm_id"))
        status = safe_int(params.get("status"))
        if alarm_id is None or status not in (0, 1):
            return "更新告警状态失败：缺少有效的告警 ID 或状态。"

        result = self.backend.update_alarm_status(
            alarm_id=alarm_id,
            status=status,
            processing_content=params.get("processing_content"),
        )
        if not result:
            return f"告警 {alarm_id} 状态更新失败。"

        self.remember_tool_state(
            request_context,
            "update_alarm_status",
            params,
            alarm_ids=[alarm_id],
        )
        return f"告警 {alarm_id} 已更新为{'已处理' if status == 1 else '未处理'}。"

    def handle_get_monitor_list(self, request_context: RequestContext, params: dict[str, Any]) -> str:
        del params
        return formatters.format_monitor_list(request_context.get_monitor_list(self.backend))

    def handle_get_monitor_detail(self, request_context: RequestContext, params: dict[str, Any]) -> str:
        monitor = self.resolve_monitor(
            request_context,
            question=str(params.get("monitor_name") or ""),
            monitor_id=safe_int(params.get("monitor_id")),
            monitor_name=params.get("monitor_name"),
        )
        if not monitor:
            return "未找到对应的监控点。"
        self.remember_tool_state(
            request_context,
            "get_monitor_detail",
            params,
            monitor=monitor,
        )
        return formatters.format_monitor_detail(monitor)

    def handle_get_weather_newest(self, request_context: RequestContext, params: dict[str, Any]) -> str:
        monitor = self.resolve_monitor(
            request_context,
            monitor_id=safe_int(params.get("monitor_id")),
            monitor_name=params.get("monitor_name"),
        )
        if not monitor:
            return "未匹配到要查询天气的监控点。"
        weather = self.backend.get_weather_newest(monitor.get("id"))
        self.remember_tool_state(
            request_context,
            "get_weather_newest",
            params,
            monitor=monitor,
        )
        return formatters.format_weather_data(monitor, weather, single=True)

    def handle_get_weather_history(self, request_context: RequestContext, params: dict[str, Any]) -> str:
        monitor = self.resolve_monitor(
            request_context,
            monitor_id=safe_int(params.get("monitor_id")),
            monitor_name=params.get("monitor_name"),
        )
        if not monitor:
            return "未匹配到要查询历史天气的监控点。"

        weather_list = self.backend.get_weather_history(
            monitor.get("id"),
            user_token=request_context.user_token,
        )
        start_time, end_time = self.extract_time_window(params)
        if weather_list and (start_time or end_time):
            weather_list = [
                item for item in weather_list
                if in_time_range(item.get("createTime"), start_time, end_time)
            ]
        self.remember_tool_state(
            request_context,
            "get_weather_history",
            params,
            monitor=monitor,
        )
        return formatters.format_weather_data(monitor, weather_list, single=False)

    def handle_update_detection_prompts(self, request_context: RequestContext, params: dict[str, Any]) -> str:
        prompts = params.get("prompts") or []
        if isinstance(prompts, str):
            prompts = [
                item.strip()
                for item in prompts.replace("，", ",").replace("、", ",").split(",")
                if item.strip()
            ]
        prompts = [str(item).strip() for item in prompts if str(item).strip()]
        if not prompts:
            return "请提供要侦测的目标，多个目标可用逗号分隔。"

        result = self.backend.update_detection_prompts(prompts, user_token=request_context.user_token)
        if result is None:
            return "侦测目标下发失败，请确认后端和算法服务已经启动。"

        translated = result if isinstance(result, list) else result.get("translated", result)
        return (
            f"已更新 Mamba-YOLO 开放世界侦测目标：{', '.join(prompts)}。\n"
            f"算法侧翻译结果：{translated}。"
        )
