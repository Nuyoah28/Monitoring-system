from __future__ import annotations

from typing import Any, Optional

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
        handler = getattr(support, f"handle_{tool_name}", None)
        if not callable(handler):
            return ""
        return handler(request_context, params)
