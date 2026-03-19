"""智能监控系统 AI Agent（项目增强版）"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import ssl
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from time import mktime
from typing import Callable, Dict, List, Optional, Sequence, Tuple
from urllib.parse import quote, urlparse

import requests

try:
    import websocket
    WebSocketApp = websocket.WebSocketApp
except ImportError:
    try:
        from websocket import WebSocketApp
        import websocket
    except ImportError as exc:
        raise ImportError(
            "请安装 websocket-client 包。\n"
            "1. 卸载错误包: pip uninstall websocket -y\n"
            "2. 安装正确包: pip install websocket-client"
        ) from exc


BACKEND_BASE_URL = "http://localhost:10215/api/v1"
BACKEND_USERNAME = "root"
BACKEND_PASSWORD = "123456"
XF_APPID = "82a9835b"
XF_API_SECRET = "OTdiMmFmZDI1ZjM0ZjlmODQwYzAxODY4"
XF_API_KEY = "a1d1ef36e1db50f361ae53fc3c55e234"
XF_HOST_URL = "https://spark-api.xf-yun.com/v1/x1"

MAX_HISTORY_MESSAGES = 6
MAX_ALARM_FETCH_PAGES = 30
ALARM_PAGE_SIZE = 100

CASE_TYPE_NAMES = {
    1: "进入危险区域",
    2: "烟雾",
    3: "区域停留",
    4: "摔倒",
    5: "明火",
    6: "吸烟",
    7: "打架",
    8: "垃圾乱放",
    9: "冰面",
    10: "电动车进楼",
    11: "载具占用车道",
    12: "挥手呼救",
}

CASE_TYPE_ALIASES = {
    1: ["危险区域", "禁区", "越界", "闯入", "入侵"],
    2: ["烟雾", "烟感", "烟气"],
    3: ["区域停留", "停留", "滞留", "逗留"],
    4: ["摔倒", "跌倒", "倒地"],
    5: ["明火", "火情", "火苗", "起火"],
    6: ["吸烟", "抽烟", "抽烟行为"],
    7: ["打架", "斗殴", "冲突"],
    8: ["垃圾乱放", "垃圾", "乱放垃圾"],
    9: ["冰面", "结冰", "地面结冰"],
    10: ["电动车进楼", "电动车", "电瓶车进楼", "电瓶车"],
    11: ["载具占用车道", "占道", "车道占用", "占用车道"],
    12: ["挥手呼救", "呼救", "求救", "挥手"],
}

WARNING_LEVEL_KEYWORDS = {
    1: ["一级", "1级", "等级1", "level1"],
    2: ["二级", "2级", "等级2", "level2"],
    3: ["三级", "3级", "等级3", "level3"],
    4: ["四级", "4级", "等级4", "level4"],
    5: ["五级", "5级", "等级5", "level5"],
}

HIGH_LEVEL_KEYWORDS = ["高等级", "高危", "严重", "紧急", "重大"]
LOW_LEVEL_KEYWORDS = ["低等级", "低危", "轻微"]
STATUS_DONE_KEYWORDS = ["已处理", "处理完成", "已处置", "已关闭", "关闭告警"]
STATUS_PENDING_KEYWORDS = ["未处理", "待处理", "未处置", "处理中", "待办"]


"""
    "你是谁",
    "浣犳槸璋?,
    "能做什么",
    "鍙互鍋氫粈涔?,
    "可以做什么",
    "支持什么",
    "链変粈涔堝姛鑳?,
    "功能",
    "介绍一下",
]
"""
LOCAL_CAPABILITY_KEYWORDS = [
    "\u4f60\u662f\u8c01",
    "\u80fd\u505a\u4ec0\u4e48",
    "\u53ef\u4ee5\u505a\u4ec0\u4e48",
    "\u652f\u6301\u4ec0\u4e48",
    "\u6709\u4ec0\u4e48\u529f\u80fd",
    "\u529f\u80fd",
    "\u4ecb\u7ecd\u4e00\u4e0b",
    "\u5e2e\u6211",
]
NON_RETRYABLE_SPARK_MARKERS = [
    "AppIdNoAuthError",
    "11200",
    "invalid api key",
    "auth",
    "unauth",
]


def contains_any(text: str, keywords: Sequence[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def normalize_text(text: str) -> str:
    return re.sub(r"[\s`~!@#$%^&*()\-_=+\[\]{}\\|;:'\",.<>/?，。！？、；：‘’“”（）【】《》]+", "", text.lower())


def unique_preserve_order(items: Sequence[str]) -> List[str]:
    result: List[str] = []
    seen = set()
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def safe_int(value, default: Optional[int] = None) -> Optional[int]:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def is_non_retryable_spark_error(error: Exception | str) -> bool:
    message = str(error).lower()
    return any(marker.lower() in message for marker in NON_RETRYABLE_SPARK_MARKERS)


def has_explicit_time_reference(question: str) -> bool:
    time1, time2 = extract_time_range(question)
    return bool(time1 or time2)


def describe_case_types(case_types: Optional[Sequence[int]]) -> str:
    if not case_types:
        return "全部类型"
    names = [CASE_TYPE_NAMES.get(case_type, f"类型{case_type}") for case_type in case_types]
    return "、".join(names)


def describe_warning_levels(levels: Optional[Sequence[int]]) -> str:
    if not levels:
        return "全部等级"
    return "、".join(f"{level}级" for level in levels)


def format_time_range(time1: Optional[str], time2: Optional[str]) -> str:
    if time1 and time2:
        return f"{time1} 至 {time2}"
    if time1:
        return f"{time1} 之后"
    if time2:
        return f"{time2} 之前"
    return "全部时间"


def parse_date_string(date_str: str) -> Optional[datetime]:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def build_day_range(dt: datetime) -> Tuple[str, str]:
    return (
        dt.strftime("%Y-%m-%d 00:00:00"),
        dt.strftime("%Y-%m-%d 23:59:59"),
    )


def extract_absolute_dates(question: str) -> List[datetime]:
    matches = re.findall(r"(20\d{2}[-/年]\d{1,2}[-/月]\d{1,2}日?)", question)
    parsed = []
    for match in matches:
        normalized = match.replace("年", "-").replace("月", "-").replace("日", "").replace("/", "-")
        dt = parse_date_string(normalized)
        if dt:
            parsed.append(dt)
    return parsed


def extract_time_range(question: str) -> Tuple[Optional[str], Optional[str]]:
    now = datetime.now()
    parsed_dates = extract_absolute_dates(question)
    if len(parsed_dates) >= 2:
        start = parsed_dates[0]
        end = parsed_dates[1]
        if start > end:
            start, end = end, start
        return build_day_range(start)[0], build_day_range(end)[1]
    if len(parsed_dates) == 1:
        return build_day_range(parsed_dates[0])

    normalized = question.replace(" ", "")
    if "今天" in normalized or "今日" in normalized:
        return build_day_range(now)
    if "昨天" in normalized:
        return build_day_range(now - timedelta(days=1))
    if contains_any(normalized, ["近3天", "最近3天", "三天内"]):
        start = now - timedelta(days=2)
        return build_day_range(start)[0], build_day_range(now)[1]
    if contains_any(normalized, ["近7天", "最近7天", "最近一周", "一周内"]):
        start = now - timedelta(days=6)
        return build_day_range(start)[0], build_day_range(now)[1]
    if contains_any(normalized, ["近30天", "最近30天", "最近一个月", "一个月内"]):
        start = now - timedelta(days=29)
        return build_day_range(start)[0], build_day_range(now)[1]
    if "本周" in normalized:
        start = now - timedelta(days=now.weekday())
        return build_day_range(start)[0], build_day_range(now)[1]
    if "本月" in normalized:
        start = now.replace(day=1)
        return build_day_range(start)[0], build_day_range(now)[1]
    return None, None


def extract_history_defer(question: str) -> int:
    normalized = question.replace(" ", "")
    if contains_any(normalized, ["今天", "今日", "24小时", "一天"]):
        return 1
    if contains_any(normalized, ["近3天", "最近3天", "三天"]):
        return 3
    if contains_any(normalized, ["近30天", "最近30天", "最近一个月", "一个月"]):
        return 30
    return 7


def parse_alarm_display_time(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    current_year = datetime.now().year
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m-%d %H:%M", "%m-%d %I:%M"):
        try:
            parsed = datetime.strptime(value, fmt)
            if fmt.startswith("%m-"):
                return parsed.replace(year=current_year)
            return parsed
        except ValueError:
            continue
    return None


def in_time_range(display_time: Optional[str], time1: Optional[str], time2: Optional[str]) -> bool:
    if not time1 and not time2:
        return True
    parsed = parse_alarm_display_time(display_time)
    if not parsed:
        return True

    start = None
    end = None
    if time1:
        try:
            start = datetime.strptime(time1, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            start = None
    if time2:
        try:
            end = datetime.strptime(time2, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            end = None

    if start and parsed < start:
        return False
    if end and parsed > end:
        return False
    return True


@dataclass
class RequestContext:
    user_token: Optional[str]
    conversation_key: Optional[str] = None
    monitor_list_cache: Optional[List[Dict]] = None

    def get_monitor_list(self, backend: "BackendClient") -> List[Dict]:
        if self.monitor_list_cache is None:
            self.monitor_list_cache = backend.get_monitor_list(user_token=self.user_token) or []
        return self.monitor_list_cache


class SparkDeskClient:
    """科大讯飞 Spark API 客户端。"""

    def __init__(self, appid: str, api_key: str, api_secret: str):
        self.appid = appid
        self.api_key = api_key
        self.api_secret = api_secret
        self.host_url = XF_HOST_URL

    def _build_auth_url(self) -> str:
        from wsgiref.handlers import format_date_time

        parsed = urlparse(self.host_url)
        host = parsed.netloc
        path = parsed.path
        date = format_date_time(mktime(datetime.now().timetuple()))
        signature_origin = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"
        signature_sha = hmac.new(
            self.api_secret.encode(),
            signature_origin.encode(),
            digestmod=hashlib.sha256,
        ).digest()
        signature = base64.b64encode(signature_sha).decode()
        authorization_origin = (
            f'api_key="{self.api_key}", algorithm="hmac-sha256", '
            f'headers="host date request-line", signature="{signature}"'
        )
        authorization = base64.b64encode(authorization_origin.encode()).decode()
        return (
            f"wss://{host}{path}"
            f"?authorization={quote(authorization, safe='')}"
            f"&date={quote(date, safe='')}"
            f"&host={quote(host, safe='')}"
        )

    def chat(
        self,
        question: str,
        context: Optional[List[Dict]] = None,
        max_retries: int = 3,
        on_chunk: Optional[Callable[[str], None]] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        context = context or []
        for attempt in range(max_retries):
            try:
                return self._chat_once(
                    question,
                    context=context,
                    on_chunk=on_chunk,
                    max_tokens=max_tokens,
                )
            except Exception as exc:
                if is_non_retryable_spark_error(exc):
                    raise Exception(str(exc)) from exc
                if attempt >= max_retries - 1:
                    raise Exception(f"连续 {max_retries} 次调用 Spark 失败: {exc}") from exc
                time.sleep(2 ** attempt)
        return ""

    def _chat_once(
        self,
        question: str,
        context: List[Dict],
        on_chunk: Optional[Callable[[str], None]] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        result_text: List[str] = []
        callback_errors: List[str] = []
        token_limit = max_tokens if max_tokens is not None else 32768

        def on_message(ws, message):
            data = json.loads(message)
            code = data.get("header", {}).get("code", -1)
            if code != 0:
                callback_errors.append(
                    f"Spark API error {code}: {data.get('header', {}).get('message', '')}"
                )
                ws.close()
                raise Exception(
                    f"Spark API 错误 {code}: {data.get('header', {}).get('message', '')}"
                )

            choices = data.get("payload", {}).get("choices", {})
            for item in choices.get("text", []):
                content = item.get("content", "")
                if content:
                    result_text.append(content)
                    if on_chunk:
                        on_chunk(content)

            if choices.get("status") == 2:
                ws.close()

        def on_error(ws, error):
            callback_errors.append(str(error))
            raise Exception(str(error))

        def on_open(ws):
            messages = [{"role": item["role"], "content": item["content"]} for item in context]
            messages.append({"role": "user", "content": question})
            request_data = {
                "header": {"app_id": self.appid},
                "parameter": {
                    "chat": {
                        "domain": "x1",
                        "max_tokens": token_limit,
                        "top_k": 6,
                        "temperature": 0.8,
                        "tools": [
                            {
                                "web_search": {"search_mode": "normal", "enable": False},
                                "type": "web_search",
                            }
                        ],
                    }
                },
                "payload": {"message": {"text": messages}},
            }
            ws.send(json.dumps(request_data, ensure_ascii=False))

        websocket.enableTrace(False)
        ws = WebSocketApp(
            self._build_auth_url(),
            on_message=on_message,
            on_error=on_error,
            on_close=lambda *args: None,
            on_open=on_open,
        )
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        if callback_errors:
            raise Exception(callback_errors[0])
        if not result_text:
            raise Exception("未收到 AI 响应，可能是网络波动或模型服务异常。")
        return "".join(result_text).strip()


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
            or "过期" in payload.get("message", "")
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
    ) -> Optional[Dict]:
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

    def get_alarm_history(self, defer: int = 7) -> Optional[Dict]:
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

    def get_realtime_alarm(self) -> Optional[Dict]:
        response = self._request("GET", "/alarm/realtime", timeout=5)
        data = response.json()
        if data.get("code") != "00000":
            return None
        return data.get("data")

    def get_monitor_list(self, user_token: Optional[str] = None) -> Optional[List[Dict]]:
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

    def get_alarm_by_id(self, alarm_id: int) -> Optional[Dict]:
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
    ) -> Optional[Dict]:
        payload = {
            "id": alarm_id,
            "status": status,
            "processingContent": processing_content,
        }
        response = self._request(
            "PUT",
            "/alarm/update",
            json=payload,
            timeout=10,
        )
        data = response.json()
        if data.get("code") != "00000":
            return None
        return data

    def get_weather_newest(self, monitor_id: int) -> Optional[Dict]:
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
    ) -> Optional[List[Dict]]:
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
        prompts: List[str],
        *,
        user_token: Optional[str] = None,
    ) -> Optional[Dict]:
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


TOOLS_SCHEMA = {
    "tools": [
        {
            "name": "get_alarm_list",
            "description": "查询告警列表、未处理告警、已处理告警、某类告警明细。",
            "parameters": {
                "case_types": "int数组，可选，例如 [5] 表示明火，[2,5] 表示烟雾和明火",
                "status": "0=未处理，1=已处理，可选",
                "warning_levels": "int数组，可选，例如 [4,5]",
                "page_size": "返回条数，默认 10",
                "time_text": "可选，例如 今天、近7天、2026-03-01 到 2026-03-07",
            },
        },
        {
            "name": "get_alarm_count",
            "description": "查询告警数量、多少条告警、多少条未处理告警、某类告警数量。",
            "parameters": {
                "case_types": "int数组，可选",
                "status": "0=未处理，1=已处理，可选",
                "warning_levels": "int数组，可选",
                "time_text": "可选",
            },
        },
        {
            "name": "get_alarm_history",
            "description": "查询告警趋势、历史走势、近几天变化。",
            "parameters": {
                "defer": "1/3/7/30，分别表示今天、近3天、近7天、近30天",
            },
        },
        {
            "name": "get_realtime_alarm",
            "description": "查询当前实时告警概况、大屏统计、当前态势。",
            "parameters": {},
        },
        {
            "name": "get_alarm_detail",
            "description": "根据告警 ID 查询单条告警详情。",
            "parameters": {"alarm_id": "告警 ID"},
        },
        {
            "name": "update_alarm_status",
            "description": "把某条告警标记为已处理或未处理。",
            "parameters": {
                "alarm_id": "告警 ID",
                "status": "0=未处理，1=已处理",
                "processing_content": "处理说明，可选",
            },
        },
        {
            "name": "get_monitor_list",
            "description": "查询监控点列表、全部监控点、有哪些摄像头。",
            "parameters": {},
        },
        {
            "name": "get_monitor_detail",
            "description": "查询某个监控点的状态、负责人、能力、视频监控信息。",
            "parameters": {
                "monitor_id": "监控点 ID，可选",
                "monitor_name": "监控点名称，可选",
            },
        },
        {
            "name": "get_weather_newest",
            "description": "查询某个监控点最新天气、温度、湿度。",
            "parameters": {
                "monitor_id": "监控点 ID，可选",
                "monitor_name": "监控点名称，可选",
            },
        },
        {
            "name": "get_weather_history",
            "description": "查询某个监控点历史天气记录。",
            "parameters": {
                "monitor_id": "监控点 ID，可选",
                "monitor_name": "监控点名称，可选",
            },
        },
        {
            "name": "update_detection_prompts",
            "description": "更新 Mamba-YOLO 开放世界检测目标，例如红色电动车、戴帽子的人。",
            "parameters": {
                "prompts": "字符串数组，例如 ['红色电动车', '戴帽子的人']",
            },
        },
    ]
}

TOOL_SELECTION_PROMPT = """你是监控系统的工具规划助手。请根据用户问题，只输出 JSON，不要输出其他解释。

输出规则：
1. 只需要一个工具时：{{"tool":"工具名","params":{{...}}}}
2. 需要多个工具时：[{{"tool":"工具名","params":{{...}}}}, {{"tool":"工具名","params":{{...}}}}]
3. 不需要调用工具时：{{"tool":"none","params":{{}}}}

约束：
- 告警类型请用 case_types 数组，值来自 1~12。
- 告警状态请用 status，0 表示未处理，1 表示已处理。
- 告警等级请用 warning_levels 数组。
- 监控点优先传 monitor_name，只有明确给出数字 ID 时才传 monitor_id。
- 用户如果明确要求“设置/添加/更新侦测目标”，请调用 update_detection_prompts。
- 用户如果明确要求“把某条告警标记为已处理/未处理”，请调用 update_alarm_status。

工具列表：
{tools_desc}

用户问题：
{question}

JSON："""


class IntelligentAgent:
    def __init__(self):
        self.backend = BackendClient(BACKEND_BASE_URL, BACKEND_USERNAME, BACKEND_PASSWORD)
        self.ai_client = SparkDeskClient(XF_APPID, XF_API_KEY, XF_API_SECRET)
        self._conversation_histories: Dict[str, List[Dict[str, str]]] = {}
        self._conversation_states: Dict[str, Dict[str, object]] = {}
        self._history_lock = threading.Lock()

    def _default_conversation_key(self, user_token: Optional[str]) -> str:
        if user_token:
            digest = hashlib.sha1(user_token.encode("utf-8")).hexdigest()[:12]
            return f"user:{digest}"
        return "anonymous:default"

    def _get_history(self, conversation_key: str) -> List[Dict[str, str]]:
        with self._history_lock:
            return list(self._conversation_histories.get(conversation_key, []))

    def _append_history(self, conversation_key: str, question: str, answer: str) -> None:
        with self._history_lock:
            history = self._conversation_histories.setdefault(conversation_key, [])
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": answer})
            if len(history) > MAX_HISTORY_MESSAGES:
                self._conversation_histories[conversation_key] = history[-MAX_HISTORY_MESSAGES:]

    def _get_conversation_state(self, conversation_key: Optional[str]) -> Dict[str, object]:
        if not conversation_key:
            return {}
        with self._history_lock:
            raw = self._conversation_states.get(conversation_key, {})
            state = dict(raw)
            if isinstance(state.get("last_tool_params"), dict):
                state["last_tool_params"] = dict(state["last_tool_params"])
            if isinstance(state.get("last_alarm_ids"), list):
                state["last_alarm_ids"] = list(state["last_alarm_ids"])
            return state

    def _update_conversation_state(self, conversation_key: Optional[str], **updates) -> None:
        if not conversation_key:
            return
        with self._history_lock:
            state = self._conversation_states.setdefault(conversation_key, {})
            for key, value in updates.items():
                if value is not None:
                    state[key] = value

    def _remember_tool_state(
        self,
        ctx: RequestContext,
        tool_name: str,
        params: Dict,
        *,
        alarm_ids: Optional[Sequence[Optional[int]]] = None,
        monitor: Optional[Dict] = None,
    ) -> None:
        if not ctx.conversation_key:
            return

        updates: Dict[str, object] = {
            "last_tool_name": tool_name,
            "last_tool_params": dict(params),
        }

        if alarm_ids is not None:
            updates["last_alarm_ids"] = [
                alarm_id
                for alarm_id in (safe_int(item) for item in alarm_ids)
                if alarm_id is not None
            ]

        if monitor:
            monitor_id = safe_int(monitor.get("id"))
            if monitor_id is not None:
                updates["last_monitor_id"] = monitor_id
            monitor_name = monitor.get("name")
            if monitor_name:
                updates["last_monitor_name"] = monitor_name

        self._update_conversation_state(ctx.conversation_key, **updates)

    def _extract_processing_content(self, question: str) -> Optional[str]:
        match = re.search(
            r"(?:\u5904\u7406\u8bf4\u660e|\u5904\u7406\u5185\u5bb9|\u5907\u6ce8)\s*[:\uff1a]?\s*(.+)$",
            question,
        )
        if match:
            return match.group(1).strip()
        return None

    def _resolve_contextual_alarm_id(self, question: str, ctx: RequestContext) -> Optional[int]:
        alarm_id = self._extract_alarm_id(question)
        if alarm_id is not None:
            return alarm_id

        if not contains_any(
            question,
            [
                "\u521a\u624d\u90a3\u4e2a",
                "\u521a\u521a\u90a3\u4e2a",
                "\u4e0a\u4e00\u4e2a\u544a\u8b66",
                "\u4e0a\u4e2a\u544a\u8b66",
                "\u4e0a\u4e00\u6761\u544a\u8b66",
                "\u8fd9\u4e2a\u544a\u8b66",
                "\u90a3\u4e2a\u544a\u8b66",
                "\u521a\u624d\u90a3\u6761",
                "\u4e0a\u4e00\u4e2a",
            ],
        ):
            return None

        state = self._get_conversation_state(ctx.conversation_key)
        alarm_ids = state.get("last_alarm_ids") or []
        if isinstance(alarm_ids, list) and alarm_ids:
            return safe_int(alarm_ids[0])
        return None

    def _build_contextual_tool_calls(self, question: str, ctx: RequestContext) -> List[Tuple[str, Dict]]:
        state = self._get_conversation_state(ctx.conversation_key)
        if not state:
            return []

        alarm_id = self._resolve_contextual_alarm_id(question, ctx)
        status = self._extract_status(question)
        if alarm_id is not None:
            if status in (0, 1) and contains_any(
                question,
                [
                    "\u6807",
                    "\u6807\u8bb0",
                    "\u5904\u7406",
                    "\u66f4\u65b0",
                    "\u6539\u6210",
                    "\u6539\u4e3a",
                    "\u8bbe",
                    "\u8bbe\u4e3a",
                    "\u5904\u7406\u5b8c\u6210",
                    "\u91cd\u65b0\u6253\u5f00",
                ],
            ):
                return [
                    (
                        "update_alarm_status",
                        {
                            "alarm_id": alarm_id,
                            "status": status,
                            "processing_content": self._extract_processing_content(question),
                        },
                    )
                ]
            if contains_any(
                question,
                [
                    "\u4e0a\u4e00\u4e2a\u544a\u8b66",
                    "\u4e0a\u4e2a\u544a\u8b66",
                    "\u4e0a\u4e00\u6761\u544a\u8b66",
                    "\u521a\u624d\u90a3\u4e2a",
                    "\u521a\u521a\u90a3\u4e2a",
                    "\u8fd9\u4e2a\u544a\u8b66",
                    "\u90a3\u4e2a\u544a\u8b66",
                    "\u8be6\u60c5",
                    "\u8be6\u7ec6",
                    "\u4fe1\u606f",
                    "\u5185\u5bb9",
                    "\u89c6\u9891",
                ],
            ):
                return [("get_alarm_detail", {"alarm_id": alarm_id})]

        if not has_explicit_time_reference(question):
            return []

        last_tool_name = state.get("last_tool_name")
        last_tool_params = dict(state.get("last_tool_params") or {})
        time1, time2 = extract_time_range(question)
        time_text = format_time_range(time1, time2) if time1 or time2 else None

        if last_tool_name in {"get_alarm_list", "get_alarm_count"}:
            if time_text:
                last_tool_params["time_text"] = time_text
            return [(str(last_tool_name), last_tool_params)]

        if last_tool_name == "get_alarm_history":
            return [("get_alarm_history", {"defer": extract_history_defer(question)})]

        if last_tool_name in {"get_weather_newest", "get_weather_history"}:
            monitor_id = safe_int(state.get("last_monitor_id"))
            monitor_name = state.get("last_monitor_name")
            if monitor_id is None and not monitor_name:
                return []
            return [
                (
                    "get_weather_history",
                    {
                        "monitor_id": monitor_id,
                        "monitor_name": monitor_name,
                        "time_text": time_text,
                    },
                )
            ]

        return []

    def _build_data_fallback_answer(self, question: str, data_summary: str) -> str:
        lines = [
            "\u6839\u636e\u5f53\u524d\u7cfb\u7edf\u6570\u636e\uff0c\u7ed3\u679c\u5982\u4e0b\uff1a",
            data_summary,
        ]
        if contains_any(question, ["\u5efa\u8bae", "\u600e\u4e48\u5904\u7406", "\u5982\u4f55\u5904\u7406", "\u600e\u4e48\u529e"]):
            lines.append(
                "\u5efa\u8bae\u4f18\u5148\u5904\u7406\u9ad8\u7b49\u7ea7\u3001\u672a\u5904\u7406\u544a\u8b66\uff0c"
                "\u5e76\u590d\u6838\u5bf9\u5e94\u76d1\u63a7\u70b9\u89c6\u9891\u548c\u73b0\u573a\u60c5\u51b5\u3002"
            )
        return "\n\n".join(lines)

    def _build_local_service_fallback(self, question: str) -> str:
        if contains_any(question, ["\u80fd\u529b", "\u4f60\u80fd\u505a\u4ec0\u4e48", "\u652f\u6301\u4ec0\u4e48", "\u4ecb\u7ecd\u4e00\u4e0b"]):
            return (
                "\u5f53\u524d\u667a\u80fd\u751f\u6210\u670d\u52a1\u4e0d\u7a33\u5b9a\uff0c"
                "\u4f46\u7cfb\u7edf\u4ecd\u652f\u6301\u8fd9\u4e9b\u80fd\u529b\uff1a"
                "\u67e5\u8be2\u544a\u8b66\u5217\u8868\u3001\u7edf\u8ba1\u5b9e\u65f6\u544a\u8b66\u3001"
                "\u67e5\u770b\u544a\u8b66\u8be6\u60c5\u3001\u67e5\u8be2\u76d1\u63a7\u70b9\u4fe1\u606f\u3001"
                "\u67e5\u8be2\u5929\u6c14\u3001\u66f4\u65b0\u544a\u8b66\u72b6\u6001\u548c\u4e0b\u53d1\u4fa6\u6d4b\u76ee\u6807\u3002"
            )
        return (
            "\u5f53\u524d\u5916\u90e8 AI \u5e94\u7b54\u670d\u52a1\u6682\u65f6\u4e0d\u7a33\u5b9a\uff0c"
            "\u4f46\u76d1\u63a7\u7cfb\u7edf\u6570\u636e\u67e5\u8be2\u4ecd\u53ef\u4ee5\u7ee7\u7eed\u4f7f\u7528\u3002"
            "\u4f60\u53ef\u4ee5\u76f4\u63a5\u8bd5\u8bd5\uff1a\u201c\u4eca\u5929\u6709\u591a\u5c11\u6761\u672a\u5904\u7406\u544a\u8b66\u201d\u3001"
            "\u201c\u67e5\u770b\u544a\u8b66 12 \u8be6\u60c5\u201d\u3001"
            "\u201c1 \u53f7\u76d1\u63a7\u70b9\u6700\u65b0\u5929\u6c14\u201d\u6216"
            "\u201c\u628a\u544a\u8b66 12 \u6807\u8bb0\u4e3a\u5df2\u5904\u7406\u201d\u3002"
        )

    def _is_local_capability_question(self, question: str) -> bool:
        return contains_any(question.lower(), [keyword.lower() for keyword in LOCAL_CAPABILITY_KEYWORDS])

    def _build_local_capability_answer(self) -> str:
        return (
            "\u6211\u662f\u201c\u667a\u884c\u62a4\u536b\u201d\u76d1\u63a7\u7cfb\u7edf\u7684\u667a\u80fd\u52a9\u624b\u3002"
            "\u76ee\u524d\u53ef\u4ee5\u5e2e\u4f60\u67e5\u8be2\u544a\u8b66\u5217\u8868\u3001\u7edf\u8ba1\u672a\u5904\u7406\u544a\u8b66\u3001"
            "\u67e5\u770b\u544a\u8b66\u8be6\u60c5\u3001\u67e5\u8be2\u76d1\u63a7\u70b9\u4fe1\u606f\u3001"
            "\u67e5\u8be2\u6700\u65b0\u6216\u5386\u53f2\u5929\u6c14\u3001"
            "\u66f4\u65b0\u544a\u8b66\u5904\u7406\u72b6\u6001\uff0c\u4ee5\u53ca\u4e0b\u53d1\u5f00\u653e\u4e16\u754c\u4fa6\u6d4b\u76ee\u6807\u3002"
            "\u4f60\u53ef\u4ee5\u76f4\u63a5\u8bf4\uff1a\u201c\u4eca\u5929\u6709\u591a\u5c11\u6761\u672a\u5904\u7406\u544a\u8b66\u201d\u3001"
            "\u201c\u67e5\u770b\u544a\u8b66 12 \u8be6\u60c5\u201d\u6216"
            "\u201c\u628a\u544a\u8b66 12 \u6807\u8bb0\u4e3a\u5df2\u5904\u7406\u201d\u3002"
        )

    def _generate_answer_with_fallback(
        self,
        *,
        question: str,
        final_prompt: str,
        history: List[Dict[str, str]],
        data_summary: str,
        on_chunk: Optional[Callable[[str], None]] = None,
        user_token: Optional[str] = None,
        conversation_key: Optional[str] = None,
        skip_primary_ai: bool = False,
    ) -> str:
        if not skip_primary_ai:
            try:
                return self.ai_client.chat(final_prompt, context=history, on_chunk=on_chunk)
            except Exception as spark_exc:
                print(f"Spark answer generation failed: {spark_exc}")

        if data_summary:
            fallback = self._build_data_fallback_answer(question, data_summary)
            if on_chunk:
                on_chunk(fallback)
            return fallback

        try:
            cbs_answer = self.backend.chat_cbs(
                question,
                user_token=user_token,
                conversation_key=conversation_key,
            )
            if cbs_answer:
                if on_chunk:
                    on_chunk(cbs_answer)
                return cbs_answer
        except Exception as cbs_exc:
            print(f"CBS answer generation failed: {cbs_exc}")

        fallback = self._build_local_service_fallback(question)
        if on_chunk:
            on_chunk(fallback)
        return fallback

    def _get_tools_desc(self) -> str:
        lines = []
        for tool in TOOLS_SCHEMA["tools"]:
            lines.append(f"- {tool['name']}: {tool['description']}")
            for param_name, param_desc in tool.get("parameters", {}).items():
                lines.append(f"  - {param_name}: {param_desc}")
        return "\n".join(lines)

    def _parse_tool_calls(self, llm_output: str) -> List[Tuple[str, Dict]]:
        llm_output = llm_output.strip()
        fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", llm_output)
        if fenced:
            llm_output = fenced.group(1).strip()
        matched = re.search(r"\{[\s\S]*\}|\[[\s\S]*\]", llm_output)
        if not matched:
            return []
        try:
            parsed = json.loads(matched.group())
        except json.JSONDecodeError:
            return []

        items = parsed if isinstance(parsed, list) else [parsed]
        result: List[Tuple[str, Dict]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            tool = item.get("tool")
            params = item.get("params") or {}
            if tool and tool != "none":
                result.append((tool, params if isinstance(params, dict) else {}))
        return result

    def _extract_case_types(self, question: str) -> List[int]:
        normalized = normalize_text(question)
        matched = []
        for case_type, aliases in CASE_TYPE_ALIASES.items():
            if any(normalize_text(alias) in normalized for alias in aliases):
                matched.append(case_type)
        return [int(item) for item in unique_preserve_order([str(item) for item in matched])]

    def _extract_warning_levels(self, question: str) -> List[int]:
        normalized = question.replace(" ", "").lower()
        levels = []
        for level, keywords in WARNING_LEVEL_KEYWORDS.items():
            if contains_any(normalized, keywords):
                levels.append(level)
        if not levels and contains_any(normalized, HIGH_LEVEL_KEYWORDS):
            levels.extend([4, 5])
        if not levels and contains_any(normalized, LOW_LEVEL_KEYWORDS):
            levels.extend([1, 2])
        return [int(level) for level in unique_preserve_order([str(level) for level in levels])]

    def _extract_status(self, question: str) -> Optional[int]:
        if contains_any(question, STATUS_PENDING_KEYWORDS):
            return 0
        if contains_any(question, STATUS_DONE_KEYWORDS):
            return 1
        return None

    def _extract_alarm_id(self, question: str) -> Optional[int]:
        patterns = [
            r"(?:告警|报警|警报|事件)\s*(?:id|ID|编号)?\s*[:：#]?\s*(\d+)",
            r"(?:id|ID)\s*[:：#]?\s*(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, question)
            if match:
                return safe_int(match.group(1))
        return None

    def _extract_monitor_id(self, question: str) -> Optional[int]:
        patterns = [
            r"(?:监控点|摄像头|监控|点位)\s*(?:id|ID|编号)?\s*[:：#]?\s*(\d+)",
            r"(\d+)\s*(?:号)?(?:监控点|摄像头|监控)",
        ]
        for pattern in patterns:
            match = re.search(pattern, question)
            if match:
                return safe_int(match.group(1))
        return None

    def _extract_detection_prompts(self, question: str) -> List[str]:
        if not contains_any(question, ["设置", "添加", "更新", "下发", "开始侦测", "开始检测", "帮我侦测", "请侦测"]):
            return []
        if not contains_any(question, ["侦测", "检测", "识别", "监测", "目标", "提示词", "prompt"]):
            return []

        candidate = question
        for prefix in ["设置", "添加", "更新", "下发", "开始侦测", "开始检测", "帮我侦测", "请侦测", "侦测", "检测", "识别", "监测"]:
            if prefix in candidate:
                candidate = candidate.split(prefix, 1)[1]
                break

        candidate = re.sub(r"^(目标|内容|提示词|prompt|一下|一下吧|一下子|为我|成|为)\s*", "", candidate)
        candidate = candidate.replace("：", ":").split(":", 1)[-1]
        candidate = re.sub(r"[。？！?]$", "", candidate)
        candidate = candidate.replace("，", ",").replace("、", ",").replace("；", ",").replace(";", ",")
        items = []
        for part in candidate.split(","):
            cleaned = part.strip()
            cleaned = re.sub(r"^(目标|物体|对象|内容)\s*", "", cleaned)
            cleaned = re.sub(r"(可以吗|行吗|吗|吧)$", "", cleaned).strip()
            if cleaned:
                items.append(cleaned)
        return unique_preserve_order(items)

    def _extract_alarm_update(self, question: str) -> Optional[Dict]:
        alarm_id = self._extract_alarm_id(question)
        if alarm_id is None:
            return None
        if not contains_any(question, ["标记", "更新", "改成", "改为", "设为", "处理完成", "重新打开"]):
            return None

        status = None
        if contains_any(question, STATUS_DONE_KEYWORDS):
            status = 1
        elif contains_any(question, ["改为未处理", "标记为未处理", "重新打开", "恢复未处理"]):
            status = 0

        if status is None:
            return None

        processing_content = None
        match = re.search(r"(?:处理说明|处理内容|备注)\s*[:：]\s*(.+)$", question)
        if match:
            processing_content = match.group(1).strip()
        return {
            "alarm_id": alarm_id,
            "status": status,
            "processing_content": processing_content,
        }

    def _resolve_monitor(
        self,
        ctx: RequestContext,
        *,
        question: str = "",
        monitor_id: Optional[int] = None,
        monitor_name: Optional[str] = None,
    ) -> Optional[Dict]:
        monitor_list = ctx.get_monitor_list(self.backend)
        if not monitor_list:
            return None

        if monitor_id is not None:
            for monitor in monitor_list:
                if safe_int(monitor.get("id")) == monitor_id:
                    return monitor

        lookup_text = monitor_name or question
        normalized_lookup = normalize_text(lookup_text)
        if not normalized_lookup:
            return None

        best_monitor = None
        best_score = -1
        for monitor in monitor_list:
            score = 0
            candidates = [
                (monitor.get("name"), 100),
                (monitor.get("department"), 70),
                (monitor.get("number"), 40),
            ]
            for raw_value, weight in candidates:
                if raw_value is None:
                    continue
                candidate = normalize_text(str(raw_value))
                if not candidate:
                    continue
                if candidate == normalized_lookup:
                    score = max(score, weight + len(candidate) * 2)
                elif candidate in normalized_lookup:
                    score = max(score, weight + len(candidate))
            if score > best_score:
                best_score = score
                best_monitor = monitor

        if best_score <= 0:
            return None
        return best_monitor

    def _fetch_alarm_pages(
        self,
        ctx: RequestContext,
        *,
        case_type: Optional[int] = None,
        status: Optional[int] = None,
        warning_level: Optional[int] = None,
        max_pages: int = MAX_ALARM_FETCH_PAGES,
    ) -> List[Dict]:
        alarms: List[Dict] = []
        seen_ids = set()

        for page_num in range(1, max_pages + 1):
            page = self.backend.get_alarm_list(
                page_num=page_num,
                page_size=ALARM_PAGE_SIZE,
                case_type=case_type,
                status=status,
                warning_level=warning_level,
                user_token=ctx.user_token,
            )
            if not page:
                break
            items = page.get("alarmList") or []
            if not items:
                break

            fresh_count = 0
            for item in items:
                alarm_id = item.get("id")
                if alarm_id not in seen_ids:
                    seen_ids.add(alarm_id)
                    alarms.append(item)
                    fresh_count += 1

            if len(items) < ALARM_PAGE_SIZE or fresh_count == 0:
                break

        return alarms

    def _query_alarm_union(
        self,
        ctx: RequestContext,
        *,
        case_types: Optional[Sequence[int]] = None,
        status: Optional[int] = None,
        warning_levels: Optional[Sequence[int]] = None,
        time1: Optional[str] = None,
        time2: Optional[str] = None,
    ) -> List[Dict]:
        case_type_list = list(case_types) if case_types else [None]
        warning_level_list = list(warning_levels) if warning_levels else [None]
        combined: List[Dict] = []
        seen_ids = set()

        for case_type in case_type_list:
            for warning_level in warning_level_list:
                alarms = self._fetch_alarm_pages(
                    ctx,
                    case_type=case_type,
                    status=status,
                    warning_level=warning_level,
                )
                for alarm in alarms:
                    alarm_id = alarm.get("id")
                    if alarm_id in seen_ids:
                        continue
                    if not in_time_range(alarm.get("date"), time1, time2):
                        continue
                    seen_ids.add(alarm_id)
                    combined.append(alarm)

        combined.sort(
            key=lambda item: parse_alarm_display_time(item.get("date")) or datetime.min,
            reverse=True,
        )
        return combined

    def _monitor_abilities(self, monitor: Dict) -> List[str]:
        abilities = []
        for item in monitor.get("ability") or []:
            if item.get("checked"):
                abilities.append(item.get("name"))
        return abilities

    def _describe_alarm_filters(
        self,
        *,
        case_types: Optional[Sequence[int]] = None,
        status: Optional[int] = None,
        warning_levels: Optional[Sequence[int]] = None,
        time1: Optional[str] = None,
        time2: Optional[str] = None,
    ) -> str:
        parts = [f"类型：{describe_case_types(case_types)}"]
        if status is None:
            parts.append("状态：全部")
        else:
            parts.append("状态：已处理" if status == 1 else "状态：未处理")
        parts.append(f"等级：{describe_warning_levels(warning_levels)}")
        parts.append(f"时间：{format_time_range(time1, time2)}")
        return "，".join(parts)

    def _format_alarm_items(
        self,
        alarms: Sequence[Dict],
        *,
        title: str,
        total_count: Optional[int] = None,
    ) -> str:
        if not alarms:
            return f"{title}：暂无符合条件的告警。"

        total = total_count if total_count is not None else len(alarms)
        lines = [f"{title}：共 {total} 条。", ""]
        for index, alarm in enumerate(alarms[:10], start=1):
            lines.append(
                f"{index}. ID {alarm.get('id', '-')}"
                f" | 事件 {alarm.get('eventName', '未知')}"
                f" | 监控点 {alarm.get('name', '未知')}"
                f" | 区域 {alarm.get('department', '未知')}"
                f" | 等级 {alarm.get('level', '未知')}"
                f" | 状态 {alarm.get('deal', '未知')}"
                f" | 时间 {alarm.get('date', '未知')}"
            )
            if alarm.get("content"):
                lines.append(f"   处置说明：{alarm.get('content')}")
        if total > 10:
            lines.append(f"... 其余 {total - 10} 条未展开。")
        return "\n".join(lines)

    def _format_alarm_count(
        self,
        count: int,
        *,
        case_types: Optional[Sequence[int]] = None,
        status: Optional[int] = None,
        warning_levels: Optional[Sequence[int]] = None,
        time1: Optional[str] = None,
        time2: Optional[str] = None,
    ) -> str:
        desc = self._describe_alarm_filters(
            case_types=case_types,
            status=status,
            warning_levels=warning_levels,
            time1=time1,
            time2=time2,
        )
        return f"告警数量统计：{count} 条。\n筛选条件：{desc}"

    def _format_alarm_history(self, history_data: Dict, defer: int) -> str:
        if not history_data:
            return "暂无告警趋势数据。"

        label = {1: "今天", 3: "近3天", 7: "近7天", 30: "近30天"}.get(defer, f"近{defer}天")
        lines = [f"告警趋势概览（{label}）：", ""]

        for title, key in [("总量趋势", "graph1"), ("区域分布", "graph2"), ("类型分布", "graph3")]:
            graph = history_data.get(key) or []
            if not graph:
                continue
            lines.append(f"{title}：")
            for item in graph[:12]:
                lines.append(f"- {item.get('period', '未知')}: {item.get('cnt', 0)}")
            lines.append("")

        return "\n".join(lines).strip()

    def _format_realtime_data(self, realtime_data: Dict) -> str:
        if not realtime_data:
            return "暂无实时告警数据。"

        total = realtime_data.get("alarmTotal") or {}
        lines = [
            "实时告警概况：",
            f"- 总告警数：{total.get('total', 0)}",
            f"- 今日新增：{total.get('todayNew', 0)}",
            f"- 较昨日变化：{total.get('dayChange', 0)}",
            "",
        ]
        case_type_list = realtime_data.get("alarmCaseTypeTotalList") or []
        if case_type_list:
            lines.append("按类型统计：")
            for item in case_type_list:
                lines.append(
                    f"- {item.get('caseTypeName', '未知')}: 今日 {item.get('todayNew', 0)} 条，累计 {item.get('total', 0)} 条"
                )
        return "\n".join(lines)

    def _format_weather_data(self, monitor: Optional[Dict], data, *, single: bool) -> str:
        monitor_label = monitor.get("name") if monitor else "该监控点"
        if not data:
            return f"{monitor_label}暂无天气数据。"

        if single:
            return (
                f"{monitor_label}最新天气："
                f"温度 {data.get('temperature', '未知')}℃，"
                f"湿度 {data.get('humidity', '未知')}%，"
                f"天气 {data.get('weather', '未知')}，"
                f"时间 {data.get('createTime', '未知')}。"
            )

        lines = [f"{monitor_label}历史天气记录：共 {len(data)} 条。", ""]
        for index, item in enumerate(data[:10], start=1):
            lines.append(
                f"{index}. 温度 {item.get('temperature', '未知')}℃"
                f" | 湿度 {item.get('humidity', '未知')}%"
                f" | 天气 {item.get('weather', '未知')}"
                f" | 时间 {item.get('createTime', '未知')}"
            )
        if len(data) > 10:
            lines.append(f"... 其余 {len(data) - 10} 条未展开。")
        return "\n".join(lines)

    def _format_monitor_list(self, monitor_list: Sequence[Dict]) -> str:
        if not monitor_list:
            return "暂无监控点数据。"

        lines = [f"监控点列表：共 {len(monitor_list)} 个。", ""]
        for index, monitor in enumerate(monitor_list[:10], start=1):
            abilities = self._monitor_abilities(monitor)
            lines.append(
                f"{index}. {monitor.get('name', '未知')} (ID {monitor.get('id', '-')})"
                f" | 区域 {monitor.get('department', '未知')}"
                f" | 负责人 {monitor.get('leader', '未知')}"
                f" | 状态 {'运行中' if monitor.get('running') else '已停止'}"
                f" | 告警次数 {monitor.get('alarmCnt', 0)}"
            )
            if abilities:
                lines.append(f"   已开能力：{'、'.join(abilities)}")
        if len(monitor_list) > 10:
            lines.append(f"... 其余 {len(monitor_list) - 10} 个未展开。")
        return "\n".join(lines)

    def _format_monitor_detail(self, monitor: Optional[Dict]) -> str:
        if not monitor:
            return "未找到对应的监控点。"
        abilities = self._monitor_abilities(monitor)
        lines = [
            f"监控点详情：{monitor.get('name', '未知')}",
            f"- ID：{monitor.get('id', '-')}",
            f"- 区域：{monitor.get('department', '未知')}",
            f"- 负责人：{monitor.get('leader', '未知')}",
            f"- 状态：{'运行中' if monitor.get('running') else '已停止'}",
            f"- 告警次数：{monitor.get('alarmCnt', 0)}",
            f"- 视频流：{monitor.get('video', '暂无')}",
        ]
        if abilities:
            lines.append(f"- 已开能力：{'、'.join(abilities)}")
        return "\n".join(lines)

    def _rule_based_tool_calls(self, question: str, ctx: RequestContext) -> List[Tuple[str, Dict]]:
        tool_calls: List[Tuple[str, Dict]] = []
        case_types = self._extract_case_types(question)
        warning_levels = self._extract_warning_levels(question)
        status = self._extract_status(question)
        time1, time2 = extract_time_range(question)
        time_text = format_time_range(time1, time2) if time1 or time2 else None

        prompts = self._extract_detection_prompts(question)
        if prompts:
            tool_calls.append(("update_detection_prompts", {"prompts": prompts}))

        alarm_update = self._extract_alarm_update(question)
        if alarm_update:
            tool_calls.append(("update_alarm_status", alarm_update))

        alarm_id = self._extract_alarm_id(question)
        if alarm_id is not None and contains_any(question, ["详情", "详细", "信息", "内容", "视频"]):
            tool_calls.append(("get_alarm_detail", {"alarm_id": alarm_id}))

        weather_requested = contains_any(question, ["天气", "温度", "湿度"])
        alarm_requested = contains_any(question, ["告警", "报警", "警报", "事件", "异常"])
        monitor_requested = contains_any(question, ["监控", "摄像头", "监控点", "点位"])
        count_requested = contains_any(question, ["数量", "多少", "几条", "几起", "总数", "统计"])
        history_requested = contains_any(question, ["趋势", "历史", "走势", "变化"])
        realtime_requested = contains_any(question, ["实时", "概况", "总览", "态势", "大屏"])
        list_requested = contains_any(question, ["列表", "明细", "哪些", "列出", "查询", "看看", "有没有"])

        if weather_requested:
            params = {
                "monitor_id": self._extract_monitor_id(question),
                "monitor_name": None,
            }
            resolved = self._resolve_monitor(ctx, question=question, monitor_id=params["monitor_id"])
            if resolved:
                params["monitor_name"] = resolved.get("name")
                params["monitor_id"] = resolved.get("id")
            if history_requested or contains_any(question, ["记录", "最近天气"]):
                tool_calls.append(("get_weather_history", params))
            else:
                tool_calls.append(("get_weather_newest", params))

        if alarm_requested:
            if realtime_requested and not count_requested and not list_requested:
                tool_calls.append(("get_realtime_alarm", {}))
            elif history_requested:
                tool_calls.append(("get_alarm_history", {"defer": extract_history_defer(question)}))
            elif count_requested:
                tool_calls.append(
                    (
                        "get_alarm_count",
                        {
                            "case_types": case_types,
                            "status": status,
                            "warning_levels": warning_levels,
                            "time_text": time_text,
                        },
                    )
                )
            else:
                if list_requested or status is not None or case_types or warning_levels:
                    tool_calls.append(
                        (
                            "get_alarm_list",
                            {
                                "case_types": case_types,
                                "status": status,
                                "warning_levels": warning_levels,
                                "page_size": 10,
                                "time_text": time_text,
                            },
                        )
                    )

        if monitor_requested and not weather_requested:
            resolved = self._resolve_monitor(ctx, question=question)
            if resolved or contains_any(question, ["负责人", "运行", "在线", "离线", "能力", "状态", "视频"]):
                tool_calls.append(
                    (
                        "get_monitor_detail",
                        {
                            "monitor_id": resolved.get("id") if resolved else self._extract_monitor_id(question),
                            "monitor_name": resolved.get("name") if resolved else None,
                        },
                    )
                )
            elif list_requested or contains_any(question, ["全部", "所有", "有哪些"]):
                tool_calls.append(("get_monitor_list", {}))

        deduped: List[Tuple[str, Dict]] = []
        seen = set()
        for tool_name, params in tool_calls:
            key = (tool_name, json.dumps(params, ensure_ascii=False, sort_keys=True))
            if key not in seen:
                seen.add(key)
                deduped.append((tool_name, params))
        return deduped

    def _llm_tool_calls(self, question: str) -> List[Tuple[str, Dict]]:
        tool_prompt = TOOL_SELECTION_PROMPT.format(
            tools_desc=self._get_tools_desc(),
            question=question,
        )
        response = self.ai_client.chat(tool_prompt, context=[], max_tokens=512)
        return self._parse_tool_calls(response)

    def _extract_time_range_from_params(self, params: Dict) -> Tuple[Optional[str], Optional[str]]:
        time_text = str(params.get("time_text") or "").strip()
        if not time_text:
            return None, None
        return extract_time_range(time_text)

    def _execute_tool(self, tool_name: str, params: Dict, ctx: RequestContext) -> Optional[str]:
        if tool_name == "get_alarm_list":
            case_types = params.get("case_types") or self._extract_case_types(str(params))
            status = safe_int(params.get("status"))
            warning_levels = params.get("warning_levels") or []
            if not isinstance(case_types, list):
                case_types = [safe_int(case_types)] if case_types is not None else []
            case_types = [safe_int(item) for item in case_types if safe_int(item) is not None]
            if not isinstance(warning_levels, list):
                warning_levels = [safe_int(warning_levels)] if warning_levels is not None else []
            warning_levels = [safe_int(item) for item in warning_levels if safe_int(item) is not None]
            time1, time2 = self._extract_time_range_from_params(params)
            alarms = self._query_alarm_union(
                ctx,
                case_types=case_types or None,
                status=status,
                warning_levels=warning_levels or None,
                time1=time1,
                time2=time2,
            )
            page_size = safe_int(params.get("page_size"), 10) or 10
            self._remember_tool_state(
                ctx,
                tool_name,
                params,
                alarm_ids=[alarm.get("id") for alarm in alarms[:page_size]],
            )
            return self._format_alarm_items(
                alarms[:page_size],
                title="告警列表",
                total_count=len(alarms),
            )

        if tool_name == "get_alarm_count":
            case_types = params.get("case_types") or []
            if not isinstance(case_types, list):
                case_types = [safe_int(case_types)] if case_types is not None else []
            case_types = [safe_int(item) for item in case_types if safe_int(item) is not None]

            warning_levels = params.get("warning_levels") or []
            if not isinstance(warning_levels, list):
                warning_levels = [safe_int(warning_levels)] if warning_levels is not None else []
            warning_levels = [safe_int(item) for item in warning_levels if safe_int(item) is not None]

            status = safe_int(params.get("status"))
            time1, time2 = self._extract_time_range_from_params(params)

            alarms = self._query_alarm_union(
                ctx,
                case_types=case_types or None,
                status=status,
                warning_levels=warning_levels or None,
                time1=time1,
                time2=time2,
            )
            self._remember_tool_state(
                ctx,
                tool_name,
                params,
                alarm_ids=[alarm.get("id") for alarm in alarms[:10]],
            )
            return self._format_alarm_count(
                len(alarms),
                case_types=case_types or None,
                status=status,
                warning_levels=warning_levels or None,
                time1=time1,
                time2=time2,
            )

        if tool_name == "get_alarm_history":
            defer = safe_int(params.get("defer"), 7) or 7
            history = self.backend.get_alarm_history(defer=defer)
            self._remember_tool_state(ctx, tool_name, params)
            return self._format_alarm_history(history, defer)

        if tool_name == "get_realtime_alarm":
            realtime = self.backend.get_realtime_alarm()
            return self._format_realtime_data(realtime)

        if tool_name == "get_alarm_detail":
            alarm_id = safe_int(params.get("alarm_id"))
            if alarm_id is None:
                return "缺少告警 ID。"
            alarm = self.backend.get_alarm_by_id(alarm_id)
            if not alarm:
                return f"未找到 ID 为 {alarm_id} 的告警。"
            self._remember_tool_state(ctx, "get_alarm_detail", params, alarm_ids=[alarm_id])
            return self._format_alarm_items([alarm], title="告警详情", total_count=1)

        if tool_name == "update_alarm_status":
            alarm_id = safe_int(params.get("alarm_id"))
            status = safe_int(params.get("status"))
            if alarm_id is None or status not in (0, 1):
                return "更新告警状态失败：缺少有效的告警 ID 或状态。"
            processing_content = params.get("processing_content")
            result = self.backend.update_alarm_status(
                alarm_id=alarm_id,
                status=status,
                processing_content=processing_content,
            )
            if not result:
                return f"告警 {alarm_id} 状态更新失败。"
            self._remember_tool_state(ctx, tool_name, params, alarm_ids=[alarm_id])
            return f"告警 {alarm_id} 已更新为{'已处理' if status == 1 else '未处理'}。"

        if tool_name == "get_monitor_list":
            monitor_list = ctx.get_monitor_list(self.backend)
            return self._format_monitor_list(monitor_list)

        if tool_name == "get_monitor_detail":
            monitor = self._resolve_monitor(
                ctx,
                question=str(params.get("monitor_name") or ""),
                monitor_id=safe_int(params.get("monitor_id")),
                monitor_name=params.get("monitor_name"),
            )
            if not monitor:
                return "未找到对应的监控点。"
            self._remember_tool_state(ctx, tool_name, params, monitor=monitor)
            return self._format_monitor_detail(monitor)

        if tool_name == "get_weather_newest":
            monitor = self._resolve_monitor(
                ctx,
                question="",
                monitor_id=safe_int(params.get("monitor_id")),
                monitor_name=params.get("monitor_name"),
            )
            if not monitor:
                return "未匹配到要查询天气的监控点。"
            weather = self.backend.get_weather_newest(monitor.get("id"))
            self._remember_tool_state(ctx, tool_name, params, monitor=monitor)
            return self._format_weather_data(monitor, weather, single=True)

        if tool_name == "get_weather_history":
            monitor = self._resolve_monitor(
                ctx,
                question="",
                monitor_id=safe_int(params.get("monitor_id")),
                monitor_name=params.get("monitor_name"),
            )
            if not monitor:
                return "未匹配到要查询历史天气的监控点。"
            weather_list = self.backend.get_weather_history(
                monitor.get("id"),
                user_token=ctx.user_token,
            )
            time1, time2 = self._extract_time_range_from_params(params)
            if weather_list and (time1 or time2):
                weather_list = [
                    item for item in weather_list
                    if in_time_range(item.get("createTime"), time1, time2)
                ]
            self._remember_tool_state(ctx, tool_name, params, monitor=monitor)
            return self._format_weather_data(monitor, weather_list, single=False)

        if tool_name == "update_detection_prompts":
            prompts = params.get("prompts") or []
            if isinstance(prompts, str):
                prompts = [
                    item.strip()
                    for item in prompts.replace("，", ",").replace("、", ",").split(",")
                    if item.strip()
                ]
            prompts = unique_preserve_order([str(item).strip() for item in prompts if str(item).strip()])
            if not prompts:
                return "请提供要侦测的目标，多个目标可用逗号分隔。"
            result = self.backend.update_detection_prompts(prompts, user_token=ctx.user_token)
            if result is None:
                return "侦测目标下发失败，请确认后端和算法服务已经启动。"
            translated = result if isinstance(result, list) else result.get("translated", result)
            return (
                f"已更新 Mamba-YOLO 开放世界侦测目标：{', '.join(prompts)}。"
                f"算法侧翻译结果：{translated}。"
            )

        return None

    def process_question(
        self,
        question: str,
        on_chunk: Optional[Callable[[str], None]] = None,
        user_token: Optional[str] = None,
        conversation_key: Optional[str] = None,
        stream_mode: str = "default",
    ) -> str:
        question = (question or "").strip()
        if not question:
            return "问题不能为空。"

        conversation_key = conversation_key or self._default_conversation_key(user_token)
        ctx = RequestContext(user_token=user_token, conversation_key=conversation_key)

        print(f"\n用户问题: {question}")
        if on_chunk and stream_mode == "ws":
            on_chunk("正在分析您的问题...\n\n")

        if self._is_local_capability_question(question):
            answer = self._build_local_capability_answer()
            if on_chunk:
                if stream_mode == "ws":
                    on_chunk("[REPLACE]")
                on_chunk(answer)
            self._append_history(conversation_key, question, answer)
            return answer

        tool_calls = self._rule_based_tool_calls(question, ctx)
        if not tool_calls:
            tool_calls = self._build_contextual_tool_calls(question, ctx)
        skip_primary_ai = False
        if not tool_calls:
            try:
                tool_calls = self._llm_tool_calls(question)
            except Exception as exc:
                print(f"工具规划失败，回退为纯知识问答: {exc}")
                skip_primary_ai = is_non_retryable_spark_error(exc)
                tool_calls = []

        data_parts = []
        for tool_name, tool_params in tool_calls:
            try:
                result = self._execute_tool(tool_name, tool_params, ctx)
                if result:
                    data_parts.append(f"【{tool_name}】\n{result}")
            except Exception as exc:
                data_parts.append(f"【{tool_name}】\n执行失败：{exc}")

        data_summary = "\n\n".join(data_parts)

        system_prompt = """你是“智行护卫”监控系统里的智能助手小城，需要结合项目内的真实数据来回答。

回答要求：
1. 优先使用系统数据，不要编造监控点、告警数量、天气等事实。
2. 如果执行了更新类操作，要明确告诉用户已经执行了什么。
3. 如果数据不足以回答，要直接说明缺什么，不要假装查到了。
4. 回答用中文，风格专业、清晰、简洁，尽量先给结论，再给建议。
5. 如果用户在问项目能力，也可以结合本系统支持的监控、告警、天气、开放世界检测等模块回答。"""

        if data_summary:
            final_prompt = (
                f"{system_prompt}\n\n"
                f"用户问题：{question}\n\n"
                f"系统数据：\n{data_summary}\n\n"
                f"请基于这些系统数据回答用户，并在必要时给出简短处置建议。"
            )
        else:
            final_prompt = (
                f"{system_prompt}\n\n"
                f"用户问题：{question}\n\n"
                f"如果这是知识类问题，请直接回答；"
                f"如果是需要系统数据的问题但当前没有查到数据，请明确说明。"
            )

        history = self._get_history(conversation_key)
        try:
            if on_chunk and stream_mode == "ws":
                on_chunk("[REPLACE]")
            answer = self._generate_answer_with_fallback(
                question=question,
                final_prompt=final_prompt,
                history=history,
                data_summary=data_summary,
                on_chunk=on_chunk,
                user_token=user_token,
                conversation_key=conversation_key,
                skip_primary_ai=skip_primary_ai,
            )
            self._append_history(conversation_key, question, answer)
            return answer
        except Exception as exc:
            print(f"AI 响应生成失败: {exc}")
            fallback = data_summary or f"抱歉，AI 服务暂时不可用。错误信息：{exc}"
            if not data_summary:
                fallback = self._build_local_service_fallback(question)
            if on_chunk:
                if stream_mode == "ws" and not data_summary:
                    on_chunk("[REPLACE]")
                on_chunk(fallback)
            self._append_history(conversation_key, question, fallback)
            return fallback

    def chat(
        self,
        question: str,
        on_chunk: Optional[Callable[[str], None]] = None,
        user_token: Optional[str] = None,
        conversation_key: Optional[str] = None,
        stream_mode: str = "default",
    ) -> str:
        return self.process_question(
            question,
            on_chunk=on_chunk,
            user_token=user_token,
            conversation_key=conversation_key,
            stream_mode=stream_mode,
        )


def main():
    print("=" * 60)
    print("智能监控系统 AI Agent")
    print("=" * 60)
    print("输入 exit 或 quit 退出。\n")

    agent = IntelligentAgent()
    print("Agent 初始化成功。")

    while True:
        try:
            question = input("\n请输入问题: ").strip()
            if not question:
                continue
            if question.lower() in {"exit", "quit"}:
                print("再见。")
                break
            answer = agent.process_question(question)
            print("\n" + "=" * 60)
            print(answer)
            print("=" * 60)
        except KeyboardInterrupt:
            print("\n再见。")
            break
        except Exception as exc:
            print(f"\n处理失败: {exc}")


if __name__ == "__main__":
    main()
