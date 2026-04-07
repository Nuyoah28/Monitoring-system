from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class RequestContext:
    user_token: Optional[str]
    conversation_key: str
    monitor_list_cache: Optional[list[dict[str, Any]]] = None

    def get_monitor_list(self, tools: Any) -> list[dict[str, Any]]:
        if self.monitor_list_cache is None:
            self.monitor_list_cache = tools.get_monitor_list(user_token=self.user_token) or []
        return self.monitor_list_cache
