from __future__ import annotations

from typing import Any, Callable, Optional, cast
from urllib.parse import quote

import requests

from agent_core.backend_client import BackendClient
from agent_core.tools.alarm_tool import AlarmTool
from agent_core.tools.cbs_tool import CBSTool
from agent_core.tools.detection_tool import DetectionTool
from agent_core.tools.monitor_tool import MonitorTool
from agent_core.tools.weather_tool import WeatherTool


class ToolGateway:
    def __init__(self, backend: BackendClient):
        self.backend = backend
        self.alarm = AlarmTool(backend)
        self.monitor = MonitorTool(backend)
        self.weather = WeatherTool(backend)
        self.detection = DetectionTool(backend)
        self.cbs = CBSTool(backend)

    def get_alarm_list(
        self,
        *,
        page_num: int = 1,
        page_size: int = 10,
        case_type: Optional[int] = None,
        status: Optional[int] = None,
        warning_level: Optional[int] = None,
        user_token: Optional[str] = None,
    ) -> Optional[dict]:
        return self.alarm.get_alarm_list(
            page_num=page_num,
            page_size=page_size,
            case_type=case_type,
            status=status,
            warning_level=warning_level,
            user_token=user_token,
        )

    def get_alarm_history(self, defer: int = 7) -> Optional[dict]:
        return self.alarm.get_alarm_history(defer=defer)

    def get_realtime_alarm(self) -> Optional[dict]:
        return self.alarm.get_realtime_alarm()

    def get_alarm_by_id(self, alarm_id: int) -> Optional[dict]:
        return self.alarm.get_alarm_detail(alarm_id)

    def update_alarm_status(
        self,
        alarm_id: int,
        status: int,
        processing_content: Optional[str] = None,
    ) -> Optional[dict]:
        return self.alarm.update_alarm_status(
            alarm_id=alarm_id,
            status=status,
            processing_content=processing_content,
        )

    def get_monitor_list(self, user_token: Optional[str] = None) -> Optional[list[dict]]:
        return self.monitor.get_monitor_list(user_token=user_token)

    def get_weather_newest(self, monitor_id: int) -> Optional[dict]:
        return self.weather.get_weather_newest(monitor_id=monitor_id)

    def get_weather_history(self, monitor_id: int, *, user_token: Optional[str] = None) -> Optional[list[dict]]:
        return self.weather.get_weather_history(monitor_id=monitor_id, user_token=user_token)

    def update_detection_prompts(self, prompts: list[str], *, user_token: Optional[str] = None) -> Optional[dict]:
        return self.detection.update_detection_prompts(prompts=prompts, user_token=user_token)

    def chat_cbs(
        self,
        message: str,
        *,
        user_token: Optional[str] = None,
        conversation_key: Optional[str] = None,
    ) -> Optional[str]:
        return self.cbs.chat(
            message=message,
            user_token=user_token,
            conversation_key=conversation_key,
        )

    def execute(self, tool_name: str, params: dict[str, Any], support: Any, request_context: Any) -> str:
        if tool_name == "web_access":
            return self.web_access(params)
        handler = getattr(support, f"handle_{tool_name}", None)
        if not callable(handler):
            return ""
        handler_fn = cast(Callable[[Any, dict[str, Any]], Any], handler)
        result = handler_fn(request_context, params)
        return result if isinstance(result, str) else str(result or "")

    def web_access(self, params: dict[str, Any]) -> str:
        action = str(params.get("action") or "search").strip().lower()
        query = str(params.get("query") or "").strip()
        url = str(params.get("url") or "").strip()

        if action == "fetch":
            if not url:
                return "web_access 需要 url 参数用于 fetch。"
            if not url.startswith(("http://", "https://")):
                url = f"https://{url}"
            try:
                response = requests.get(
                    url,
                    timeout=15,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/124.0.0.0 Safari/537.36"
                        )
                    },
                )
                response.raise_for_status()
                text = response.text.strip().replace("\r\n", "\n")
                if len(text) > 12000:
                    text = text[:12000] + "\n...(内容已截断)"
                return f"网页抓取结果（{url}）：\n{text}"
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else None
                if status == 403:
                    return self._fetch_via_jina_or_hint(url)
                raise
            except Exception:
                return self._fetch_via_jina_or_hint(url)

        if not query:
            return "web_access 需要 query 参数用于 search。"
        search_url = f"https://duckduckgo.com/?q={quote(query)}"
        return (
            "web_access 已构建联网检索入口。\n"
            f"建议访问：{search_url}\n"
            "如需直接抓取，请改用 action=fetch 并提供 url。"
        )

    def _fetch_via_jina_or_hint(self, url: str) -> str:
        try:
            jina_url = "https://r.jina.ai/http://" + url.replace("https://", "").replace("http://", "")
            response = requests.get(jina_url, timeout=20)
            response.raise_for_status()
            text = response.text.strip().replace("\r\n", "\n")
            if len(text) > 12000:
                text = text[:12000] + "\n...(内容已截断)"
            return (
                f"网页直连被拦截（403），已使用 Jina 代理获取内容。\n"
                f"原始URL：{url}\n"
                f"代理URL：{jina_url}\n\n"
                f"{text}"
            )
        except Exception:
            return (
                "联网访问失败：目标网站可能开启了反爬策略（如 403）。\n"
                f"目标URL：{url}\n"
                "建议：\n"
                "1) 使用浏览器/CDP 模式访问后再提取内容。\n"
                "2) 或让我先尝试搜索该网页标题再汇总公开摘要。"
            )
