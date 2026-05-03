from __future__ import annotations

import threading
from typing import Optional

import requests


class BackendClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.service_token: Optional[str] = None
        self._token_lock = threading.Lock()

    @staticmethod
    def _create_session() -> requests.Session:
        session = requests.Session()
        session.trust_env = False
        return session

    @staticmethod
    def _token_expired(response: requests.Response) -> bool:
        try:
            payload = response.json()
        except Exception:
            return response.status_code == 401

        code = str(payload.get("code", "")).lower()
        message = str(payload.get("message", "")).lower()
        return (
            response.status_code == 401
            or "token" in code
            or "token" in message
            or "过期" in str(payload.get("message", ""))
        )

    def _ensure_service_token(self, force_refresh: bool = False) -> Optional[str]:
        with self._token_lock:
            if self.service_token and not force_refresh:
                return self.service_token

            with self._create_session() as session:
                response = session.post(
                    f"{self.base_url}/user/login",
                    json={"userName": self.username, "password": self.password},
                    timeout=5,
                )
                response.raise_for_status()
                data = response.json()
                if data.get("code") != "00000" or not data.get("data", {}).get("token"):
                    raise Exception(data.get("message") or "内置账号登录失败")
                self.service_token = data["data"]["token"]
                return self.service_token

    def _request(
        self,
        method: str,
        path: str,
        *,
        user_token: Optional[str] = None,
        require_auth: bool = False,
        **kwargs,
    ) -> requests.Response:
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        headers = dict(kwargs.pop("headers", {}) or {})

        auth_token = user_token
        if not auth_token and require_auth:
            auth_token = self._ensure_service_token()
        elif not auth_token and self.service_token:
            auth_token = self.service_token

        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        with self._create_session() as session:
            response = session.request(method, url, headers=headers, **kwargs)

        if self._token_expired(response):
            if user_token:
                raise Exception("当前登录已过期，请重新登录后再试。")
            if require_auth or auth_token:
                fresh_token = self._ensure_service_token(force_refresh=True)
                headers["Authorization"] = f"Bearer {fresh_token}"
                with self._create_session() as session:
                    response = session.request(method, url, headers=headers, **kwargs)

        response.raise_for_status()
        return response

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
        params = {"pageNum": page_num, "pageSize": page_size}
        if case_type is not None:
            params["caseType"] = case_type
        if status is not None:
            params["status"] = status
        if warning_level is not None:
            params["warningLevel"] = warning_level

        response = self._request(
            "GET",
            "/alarm/query",
            params=params,
            timeout=10,
            require_auth=True,
            user_token=user_token,
        )
        data = response.json()
        if data.get("code") != "00000":
            return None
        return data.get("data")

    def get_alarm_history(self, defer: int = 7) -> Optional[dict]:
        response = self._request(
            "GET",
            "/alarm/query/cnt/history",
            params={"defer": defer},
            timeout=10,
        )
        data = response.json()
        if data.get("code") != "00000":
            return None
        return data.get("data")

    def get_realtime_alarm(self) -> Optional[dict]:
        response = self._request("GET", "/alarm/realtime", timeout=5)
        data = response.json()
        if data.get("code") != "00000":
            return None
        return data.get("data")

    def get_monitor_list(self, user_token: Optional[str] = None) -> Optional[list[dict]]:
        response = self._request(
            "GET",
            "/monitor",
            timeout=5,
            require_auth=True,
            user_token=user_token,
        )
        data = response.json()
        if data.get("code") != "00000":
            return None
        return data.get("data")

    def get_alarm_by_id(self, alarm_id: int) -> Optional[dict]:
        response = self._request("GET", f"/alarm/{alarm_id}", timeout=10)
        data = response.json()
        if data.get("code") != "00000":
            return None
        return data.get("data")

    def update_alarm_status(
        self,
        alarm_id: int,
        status: int,
        processing_content: Optional[str] = None,
    ) -> Optional[dict]:
        response = self._request(
            "PUT",
            "/alarm/update",
            json={
                "id": alarm_id,
                "status": status,
                "processingContent": processing_content,
            },
            timeout=10,
        )
        data = response.json()
        if data.get("code") != "00000":
            return None
        return data

    def get_weather_newest(self, monitor_id: int) -> Optional[dict]:
        response = self._request("GET", f"/weather/newest/{monitor_id}", timeout=10)
        data = response.json()
        if data.get("code") != "00000":
            return None
        return data.get("data")

    def get_weather_history(
        self,
        monitor_id: int,
        *,
        user_token: Optional[str] = None,
    ) -> Optional[list[dict]]:
        response = self._request(
            "GET",
            f"/weather/all/{monitor_id}",
            timeout=10,
            require_auth=True,
            user_token=user_token,
        )
        data = response.json()
        if data.get("code") != "00000":
            return None
        return data.get("data")

    def update_detection_prompts(
        self,
        prompts: list[str],
        *,
        user_token: Optional[str] = None,
    ) -> Optional[dict]:
        response = self._request(
            "POST",
            "/monitor/update_prompt",
            json={"prompts": prompts},
            timeout=10,
            require_auth=True,
            user_token=user_token,
        )
        data = response.json()
        if data.get("code") != "00000":
            return None
        return data.get("data") or {}

    def chat_cbs(
        self,
        message: str,
        *,
        user_token: Optional[str] = None,
        conversation_key: Optional[str] = None,
    ) -> Optional[str]:
        payload = {"message": message}
        if conversation_key:
            payload["id"] = conversation_key

        response = self._request(
            "POST",
            "/cbs",
            json=payload,
            timeout=20,
            require_auth=True,
            user_token=user_token,
        )
        data = response.json()
        if data.get("code") != "00000":
            return None

        result = data.get("data")
        if isinstance(result, str):
            return result.strip()
        if isinstance(result, dict):
            for key in ("answer", "content", "text"):
                value = result.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return None

    def get_owner_profile(self, *, user_token: Optional[str] = None) -> Optional[dict]:
        response = self._request(
            "GET",
            "/user/profile",
            timeout=8,
            require_auth=True,
            user_token=user_token,
        )
        data = response.json()
        if data.get("code") != "00000":
            return None
        return data.get("data")

    def get_owner_messages(self, *, user_token: Optional[str] = None) -> Optional[list[dict]]:
        response = self._request(
            "GET",
            "/system/message/getMessage",
            timeout=8,
            require_auth=True,
            user_token=user_token,
        )
        data = response.json()
        if data.get("code") != "00000":
            return None
        result = data.get("data")
        return result if isinstance(result, list) else []

    def get_owner_visitors(self, *, user_token: Optional[str] = None) -> Optional[list[dict]]:
        response = self._request(
            "GET",
            "/visitor/list",
            timeout=8,
            require_auth=True,
            user_token=user_token,
        )
        data = response.json()
        if data.get("code") != "00000":
            return None
        result = data.get("data")
        return result if isinstance(result, list) else []

    def get_owner_repairs(self, *, user_token: Optional[str] = None) -> Optional[list[dict]]:
        response = self._request(
            "GET",
            "/device-repair/list",
            timeout=8,
            require_auth=True,
            user_token=user_token,
        )
        data = response.json()
        if data.get("code") != "00000":
            return None
        result = data.get("data")
        return result if isinstance(result, list) else []

    def get_parking_realtime(
        self,
        *,
        monitor_id: int = 1,
        source: str = "real",
    ) -> Optional[dict]:
        response = self._request(
            "GET",
            "/parking/realtime",
            params={"monitorId": monitor_id, "source": source},
            timeout=8,
        )
        data = response.json()
        if data.get("code") != "00000":
            return None
        return data.get("data")

    def get_parking_traffic_summary(
        self,
        *,
        monitor_id: int = 1,
        source: str = "real",
    ) -> Optional[dict]:
        response = self._request(
            "GET",
            "/parking/traffic/summary",
            params={"monitorId": monitor_id, "source": source},
            timeout=8,
        )
        data = response.json()
        if data.get("code") != "00000":
            return None
        return data.get("data")

    def get_environment_realtime(
        self,
        *,
        monitor_id: int = 1,
    ) -> Optional[dict]:
        response = self._request(
            "GET",
            "/env/realtime",
            params={"monitorId": monitor_id},
            timeout=8,
        )
        data = response.json()
        if data.get("code") != "00000":
            return None
        return data.get("data")

    def get_environment_trend(
        self,
        *,
        monitor_id: int = 1,
        range_name: str = "day",
    ) -> Optional[list[dict]]:
        response = self._request(
            "GET",
            "/env/trend",
            params={"monitorId": monitor_id, "range": range_name},
            timeout=8,
        )
        data = response.json()
        if data.get("code") != "00000":
            return None
        result = data.get("data")
        return result if isinstance(result, list) else []
