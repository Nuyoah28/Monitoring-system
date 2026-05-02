from __future__ import annotations

# AI辅助生成：本文件中的请求身份字段与线程安全缓存增强逻辑由 GPT-5 Codex 协助完成，2026-04-04。

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class RequestContext:
    user_token: Optional[str]
    conversation_key: str
    current_time: datetime
    monitor_list_cache: Optional[list[dict[str, Any]]] = None

    def get_monitor_list(self, tools: Any) -> list[dict[str, Any]]:
        if self.monitor_list_cache is None:
            self.monitor_list_cache = tools.get_monitor_list(user_token=self.user_token) or []
        return self.monitor_list_cache
