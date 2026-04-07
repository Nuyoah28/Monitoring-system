from __future__ import annotations

import json
import re
from typing import Any

from agent_core.constants import (
    ALARM_DETAIL_KEYWORDS,
    ALARM_KEYWORDS,
    ALARM_UPDATE_HINT_KEYWORDS,
    COUNT_KEYWORDS,
    HISTORY_KEYWORDS,
    LIST_KEYWORDS,
    MONITOR_DETAIL_KEYWORDS,
    MONITOR_KEYWORDS,
    MONITOR_LIST_KEYWORDS,
    REALTIME_KEYWORDS,
    WEATHER_KEYWORDS,
)
from agent_core.core.catalog import ToolCatalog
from agent_core.intent_utils import (
    extract_alarm_id,
    extract_alarm_update,
    extract_case_types,
    extract_detection_prompts,
    extract_monitor_id,
    extract_processing_content,
    extract_status,
    extract_warning_levels,
)
from agent_core.prompts import build_tool_selection_prompt
from agent_core.utils import (
    contains_any,
    extract_history_defer,
    has_explicit_time_reference,
    is_non_retryable_spark_error,
    safe_int,
)


class ToolPlanner:
    def __init__(self, ai_client: Any, tool_catalog: ToolCatalog, support: Any):
        self.ai_client = ai_client
        self.tool_catalog = tool_catalog
        self.support = support

    def plan(self, question: str, request_context: Any) -> tuple[list[tuple[str, dict]], bool]:
        tool_calls = self._rule_based_tool_calls(question, request_context)
        if not tool_calls:
            tool_calls = self._build_contextual_tool_calls(question, request_context)

        skip_primary_ai = not getattr(self.ai_client, "is_available", True)
        if not tool_calls:
            if skip_primary_ai:
                return [], True
            try:
                tool_calls = self._llm_tool_calls(question)
            except Exception as exc:
                print(f"Tool planning failed, fallback to direct answer: {exc}")
                skip_primary_ai = is_non_retryable_spark_error(exc)
                tool_calls = []

        return self._dedupe_tool_calls(tool_calls), skip_primary_ai

    def _dedupe_tool_calls(self, tool_calls: list[tuple[str, dict]]) -> list[tuple[str, dict]]:
        deduped: list[tuple[str, dict]] = []
        seen: set[tuple[str, str]] = set()
        for tool_name, params in tool_calls:
            if not self.tool_catalog.get(tool_name):
                continue
            payload = params if isinstance(params, dict) else {}
            key = (tool_name, json.dumps(payload, ensure_ascii=False, sort_keys=True))
            if key in seen:
                continue
            seen.add(key)
            deduped.append((tool_name, payload))
        return deduped

    def _build_contextual_tool_calls(self, question: str, request_context: Any) -> list[tuple[str, dict]]:
        state = self.support.get_conversation_state(request_context.conversation_key)
        if not state:
            return []

        alarm_id = self.support.resolve_contextual_alarm_id(question, request_context)
        status = extract_status(question)
        if alarm_id is not None:
            if status in (0, 1) and contains_any(question, ALARM_UPDATE_HINT_KEYWORDS):
                return [
                    (
                        "update_alarm_status",
                        {
                            "alarm_id": alarm_id,
                            "status": status,
                            "processing_content": extract_processing_content(question),
                        },
                    )
                ]

            context_detail_markers = [
                "上一个告警",
                "上个告警",
                "上一条告警",
                "刚才那个",
                "刚刚那个",
                "这个告警",
                "那个告警",
            ]
            if contains_any(question, context_detail_markers + ALARM_DETAIL_KEYWORDS):
                return [("get_alarm_detail", {"alarm_id": alarm_id})]

        if not has_explicit_time_reference(question):
            return []

        last_tool_name = state.get("last_tool_name")
        last_tool_params = dict(state.get("last_tool_params") or {})

        if last_tool_name in {"get_alarm_list", "get_alarm_count"}:
            last_tool_params["time_text"] = question
            return [(str(last_tool_name), last_tool_params)]

        if last_tool_name == "get_alarm_history":
            return [("get_alarm_history", {"defer": extract_history_defer(question)})]

        if last_tool_name in {"get_weather_newest", "get_weather_history"}:
            monitor_id = safe_int(state.get("last_monitor_id"))
            monitor_name = state.get("last_monitor_name")
            if monitor_id is None and not monitor_name:
                return []
            return [
                (
                    "get_weather_history",
                    {
                        "monitor_id": monitor_id,
                        "monitor_name": monitor_name,
                        "time_text": question,
                    },
                )
            ]

        return []

    def _rule_based_tool_calls(self, question: str, request_context: Any) -> list[tuple[str, dict]]:
        tool_calls: list[tuple[str, dict]] = []
        case_types = extract_case_types(question)
        warning_levels = extract_warning_levels(question)
        status = extract_status(question)
        time_text = question if has_explicit_time_reference(question) else None

        prompts = extract_detection_prompts(question)
        if prompts:
            tool_calls.append(("update_detection_prompts", {"prompts": prompts}))

        alarm_update = extract_alarm_update(question)
        if alarm_update:
            tool_calls.append(("update_alarm_status", alarm_update))

        alarm_id = extract_alarm_id(question)
        alarm_detail_requested = alarm_id is not None and contains_any(question, ALARM_DETAIL_KEYWORDS)
        if alarm_detail_requested:
            tool_calls.append(("get_alarm_detail", {"alarm_id": alarm_id}))

        weather_requested = contains_any(question, WEATHER_KEYWORDS)
        web_requested = contains_any(
            question,
            ["网页", "网站", "联网", "搜索", "上网", "浏览器", "网址", "http", "https", "web"],
        )
        alarm_requested = contains_any(question, ALARM_KEYWORDS)
        monitor_requested = contains_any(question, MONITOR_KEYWORDS)
        count_requested = contains_any(question, COUNT_KEYWORDS)
        history_requested = contains_any(question, HISTORY_KEYWORDS)
        realtime_requested = contains_any(question, REALTIME_KEYWORDS)
        list_requested = contains_any(question, LIST_KEYWORDS)

        if weather_requested:
            params: dict[str, Any] = {
                "monitor_id": extract_monitor_id(question),
                "monitor_name": None,
            }
            resolved_monitor = self.support.resolve_monitor(
                request_context,
                question=question,
                monitor_id=params["monitor_id"],
            )
            if resolved_monitor:
                params["monitor_id"] = resolved_monitor.get("id")
                params["monitor_name"] = resolved_monitor.get("name")
            if history_requested or contains_any(question, ["记录", "最近天气"]):
                if time_text:
                    params["time_text"] = time_text
                tool_calls.append(("get_weather_history", params))
            else:
                tool_calls.append(("get_weather_newest", params))

        if alarm_requested and not alarm_update and not alarm_detail_requested:
            if realtime_requested and not count_requested and not list_requested:
                tool_calls.append(("get_realtime_alarm", {}))
            elif history_requested:
                tool_calls.append(("get_alarm_history", {"defer": extract_history_defer(question)}))
            elif count_requested:
                tool_calls.append(
                    (
                        "get_alarm_count",
                        {
                            "case_types": case_types,
                            "status": status,
                            "warning_levels": warning_levels,
                            "time_text": time_text,
                        },
                    )
                )
            elif list_requested or status is not None or case_types or warning_levels:
                tool_calls.append(
                    (
                        "get_alarm_list",
                        {
                            "case_types": case_types,
                            "status": status,
                            "warning_levels": warning_levels,
                            "page_size": 200,
                            "time_text": time_text,
                        },
                    )
                )

        if monitor_requested and not weather_requested:
            resolved_monitor = self.support.resolve_monitor(request_context, question=question)
            if resolved_monitor or contains_any(question, MONITOR_DETAIL_KEYWORDS):
                tool_calls.append(
                    (
                        "get_monitor_detail",
                        {
                            "monitor_id": resolved_monitor.get("id") if resolved_monitor else extract_monitor_id(question),
                            "monitor_name": resolved_monitor.get("name") if resolved_monitor else None,
                        },
                    )
                )
            elif list_requested or contains_any(question, MONITOR_LIST_KEYWORDS):
                tool_calls.append(("get_monitor_list", {}))

        if web_requested and self.tool_catalog.get("web_access"):
            url_match = re.search(r"https?://[^\s]+", question)
            if url_match:
                tool_calls.append(
                    (
                        "web_access",
                        {
                            "action": "fetch",
                            "url": url_match.group(0),
                            "query": question,
                        },
                    )
                )
            else:
                tool_calls.append(("web_access", {"action": "search", "query": question}))

        return tool_calls

    def _llm_tool_calls(self, question: str) -> list[tuple[str, dict]]:
        prompt = build_tool_selection_prompt(self.tool_catalog.describe(), question)
        response = self.ai_client.chat(prompt, context=[], max_tokens=512)
        return self._parse_tool_calls(response)

    def _parse_tool_calls(self, llm_output: str) -> list[tuple[str, dict]]:
        raw_output = (llm_output or "").strip()
        fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_output)
        if fenced:
            raw_output = fenced.group(1).strip()

        matched = re.search(r"\{[\s\S]*\}|\[[\s\S]*\]", raw_output)
        if not matched:
            return []

        try:
            parsed = json.loads(matched.group())
        except json.JSONDecodeError:
            return []

        items = parsed if isinstance(parsed, list) else [parsed]
        result: list[tuple[str, dict]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            tool_name = item.get("tool")
            params = item.get("params") or {}
            if tool_name and tool_name != "none":
                result.append((str(tool_name), params if isinstance(params, dict) else {}))
        return result
