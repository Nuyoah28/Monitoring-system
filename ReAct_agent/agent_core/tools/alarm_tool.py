from __future__ import annotations

import threading
from typing import Any, Optional

import requests


class AlarmTool:
    """告警相关后端请求工具"""

    def __init__(self, backend_client: Any):
        self.backend = backend_client

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
        return self.backend.get_alarm_list(
            page_num=page_num,
            page_size=page_size,
            case_type=case_type,
            status=status,
            warning_level=warning_level,
            user_token=user_token,
        )

    def get_alarm_history(self, defer: int = 7) -> Optional[dict]:
        return self.backend.get_alarm_history(defer=defer)

    def get_realtime_alarm(self) -> Optional[dict]:
        return self.backend.get_realtime_alarm()

    def get_alarm_detail(self, alarm_id: int) -> Optional[dict]:
        return self.backend.get_alarm_by_id(alarm_id)

    def update_alarm_status(
        self,
        alarm_id: int,
        status: int,
        processing_content: Optional[str] = None,
    ) -> Optional[dict]:
        return self.backend.update_alarm_status(
            alarm_id=alarm_id,
            status=status,
            processing_content=processing_content,
        )
