from __future__ import annotations

from typing import Any, Optional


class DetectionTool:
    """侦测目标下发后端请求工具"""

    def __init__(self, backend_client: Any):
        self.backend = backend_client

    def update_detection_prompts(
        self,
        prompts: list[str],
        *,
        user_token: Optional[str] = None,
    ) -> Optional[dict]:
        return self.backend.update_detection_prompts(
            prompts=prompts,
            user_token=user_token,
        )
