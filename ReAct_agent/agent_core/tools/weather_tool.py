from __future__ import annotations

from typing import Any, Optional


class WeatherTool:
    """天气相关后端请求工具"""

    def __init__(self, backend_client: Any):
        self.backend = backend_client

    def get_weather_newest(self, monitor_id: int) -> Optional[dict]:
        return self.backend.get_weather_newest(monitor_id=monitor_id)

    def get_weather_history(
        self,
        monitor_id: int,
        *,
        user_token: Optional[str] = None,
    ) -> Optional[list[dict]]:
        return self.backend.get_weather_history(
            monitor_id=monitor_id,
            user_token=user_token,
        )
