from __future__ import annotations

from typing import Any, Optional


class MonitorTool:
    """监控点相关后端请求工具"""

    def __init__(self, backend_client: Any):
        self.backend = backend_client

    def get_monitor_list(self, user_token: Optional[str] = None) -> Optional[list[dict]]:
        return self.backend.get_monitor_list(user_token=user_token)

    def get_monitor_detail(self, monitor_id: int) -> Optional[dict]:
        monitor_list = self.backend.get_monitor_list()
        if not monitor_list:
            return None
        for monitor in monitor_list:
            if monitor.get("id") == monitor_id:
                return monitor
        return None
