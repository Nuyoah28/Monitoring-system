from __future__ import annotations

from typing import Any, Optional


class CBSTool:
    """CBS 对话服务后端请求工具"""

    def __init__(self, backend_client: Any):
        self.backend = backend_client

    def chat(
        self,
        message: str,
        *,
        user_token: Optional[str] = None,
        conversation_key: Optional[str] = None,
    ) -> Optional[str]:
        return self.backend.chat_cbs(
            message=message,
            user_token=user_token,
            conversation_key=conversation_key,
        )
