from __future__ import annotations

import base64
import hashlib
import hmac
import json
import ssl
import time
from datetime import datetime
from time import mktime
from typing import Callable, Optional
from urllib.parse import quote, urlparse

import requests

from agent_core.config import AgentSettings
from agent_core.utils import is_non_retryable_spark_error

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


class BaseLLMClient:
    provider_name = "none"
    is_available = False

    def chat(
        self,
        question: str,
        *,
        context: Optional[list[dict[str, str]]] = None,
        max_retries: int = 3,
        on_chunk: Optional[Callable[[str], None]] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        raise NotImplementedError


class NoopLLMClient(BaseLLMClient):
    provider_name = "disabled"
    is_available = False

    def __init__(self, reason: str):
        self.reason = reason

    def chat(
        self,
        question: str,
        *,
        context: Optional[list[dict[str, str]]] = None,
        max_retries: int = 3,
        on_chunk: Optional[Callable[[str], None]] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        del question, context, max_retries, on_chunk, max_tokens
        raise RuntimeError(self.reason)


class SparkDeskClient(BaseLLMClient):
    provider_name = "spark"
    is_available = True

    def __init__(self, appid: str, api_key: str, api_secret: str, host_url: str, domain: str = "x1"):
        self.appid = appid
        self.api_key = api_key
        self.api_secret = api_secret
        self.host_url = host_url
        self.domain = domain or "x1"

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
        *,
        context: Optional[list[dict[str, str]]] = None,
        max_retries: int = 3,
        on_chunk: Optional[Callable[[str], None]] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        context = context or []
        for attempt in range(max_retries):
            try:
                return self._chat_once(
                    question=question,
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
        *,
        question: str,
        context: list[dict[str, str]],
        on_chunk: Optional[Callable[[str], None]] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        result_parts: list[str] = []
        callback_errors: list[str] = []
        token_limit = max_tokens if max_tokens is not None else 32768

        def on_message(ws, message):
            data = json.loads(message)
            code = data.get("header", {}).get("code", -1)
            if code != 0:
                callback_errors.append(
                    f"Spark API error {code}: {data.get('header', {}).get('message', '')}"
                )
                ws.close()
                return

            choices = data.get("payload", {}).get("choices", {})
            for item in choices.get("text", []):
                content = item.get("content", "")
                if content:
                    result_parts.append(content)
                    if on_chunk:
                        on_chunk(content)

            if choices.get("status") == 2:
                ws.close()

        def on_error(ws, error):
            callback_errors.append(str(error))

        def on_open(ws):
            messages = [{"role": item["role"], "content": item["content"]} for item in context]
            messages.append({"role": "user", "content": question})
            ws.send(
                json.dumps(
                    {
                        "header": {"app_id": self.appid},
                        "parameter": {
                            "chat": {
                                "domain": self.domain,
                                "max_tokens": token_limit,
                                "top_k": 6,
                                "temperature": 0.8,
                                "tools": [
                                    {
                                        "web_search": {
                                            "search_mode": "normal",
                                            "enable": False
                                        },
                                        "type": "web_search"
                                    }
                                ]
                            }
                        },
                        "payload": {"message": {"text": messages}}
                    },
                    ensure_ascii=False,
                )
            )

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
        if not result_parts:
            raise Exception("未收到 AI 响应，可能是网络波动或模型服务异常。")
        return "".join(result_parts).strip()


class OpenAICompatibleClient(BaseLLMClient):
    provider_name = "openai_compatible"
    is_available = True

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        *,
        temperature: float = 0.7,
        default_max_tokens: int = 2048,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.default_max_tokens = default_max_tokens

    def _build_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _build_messages(
        self,
        question: str,
        context: Optional[list[dict[str, str]]] = None,
    ) -> list[dict[str, str]]:
        messages = []
        for item in context or []:
            role = item.get("role")
            content = item.get("content")
            if role in {"system", "user", "assistant"} and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": question})
        return messages

    def chat(
        self,
        question: str,
        *,
        context: Optional[list[dict[str, str]]] = None,
        max_retries: int = 3,
        on_chunk: Optional[Callable[[str], None]] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": self._build_messages(question, context),
            "temperature": self.temperature,
            "max_tokens": max_tokens or self.default_max_tokens,
        }

        for attempt in range(max_retries):
            try:
                if on_chunk:
                    return self._chat_stream(payload, on_chunk)
                return self._chat_once(payload)
            except Exception as exc:
                if attempt >= max_retries - 1:
                    raise Exception(f"连续 {max_retries} 次调用 OpenAI 兼容接口失败: {exc}") from exc
                time.sleep(2 ** attempt)
        return ""

    def _chat_once(self, payload: dict) -> str:
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self._build_headers(),
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        try:
            return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            raise Exception(f"OpenAI 兼容接口返回格式异常: {data}") from exc

    def _chat_stream(self, payload: dict, on_chunk: Callable[[str], None]) -> str:
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self._build_headers(),
            json={**payload, "stream": True},
            timeout=120,
            stream=True,
        )
        response.raise_for_status()

        result_parts: list[str] = []
        response.encoding = "utf-8"
        for raw_line in response.iter_lines(decode_unicode=False):
            if not raw_line:
                continue
            try:
                line = raw_line.decode("utf-8").strip()
            except UnicodeDecodeError:
                fallback_encoding = response.apparent_encoding or response.encoding or "utf-8"
                line = raw_line.decode(fallback_encoding, errors="ignore").strip()
            if not line.startswith("data:"):
                continue
            data_str = line[5:].strip()
            if data_str == "[DONE]":
                break
            try:
                event = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            for choice in event.get("choices", []):
                delta = choice.get("delta") or {}
                content = delta.get("content")
                if content:
                    result_parts.append(content)
                    on_chunk(content)

        if not result_parts:
            raise Exception("未收到 OpenAI 兼容流式响应内容。")
        return "".join(result_parts).strip()

def create_llm_client(settings: AgentSettings) -> BaseLLMClient:
    provider_name = settings.ai_active_provider
    provider = dict(settings.ai_providers.get(provider_name) or {})
    provider_type = str(provider.get("type") or provider_name or "").strip()
    enabled = bool(provider.get("enabled", True))

    if not enabled or not provider_type:
        return NoopLLMClient("AI provider is disabled.")

    if provider_type == "spark":
        app_id = str(provider.get("app_id") or settings.spark_app_id or "").strip()
        api_key = str(provider.get("api_key") or settings.spark_api_key or "").strip()
        api_secret = str(provider.get("api_secret") or settings.spark_api_secret or "").strip()
        host_url = str(provider.get("host_url") or settings.spark_host_url or "").strip()
        domain = str(provider.get("domain") or "x1").strip()
        if not (app_id and api_key and api_secret and host_url):
            return NoopLLMClient("Spark provider is not configured.")
        return SparkDeskClient(
            appid=app_id,
            api_key=api_key,
            api_secret=api_secret,
            host_url=host_url,
            domain=domain,
        )

    if provider_type == "openai_compatible":
        base_url = str(provider.get("base_url") or settings.openai_base_url or "").strip()
        api_key = str(provider.get("api_key") or settings.openai_api_key or "").strip()
        model = str(provider.get("model") or settings.openai_model or "").strip()
        temperature = float(provider.get("temperature", 0.7))
        max_tokens = int(provider.get("max_tokens", 2048))
        if not (base_url and model):
            return NoopLLMClient("OpenAI compatible provider is not configured.")
        return OpenAICompatibleClient(
            base_url=base_url,
            api_key=api_key,
            model=model,
            temperature=temperature,
            default_max_tokens=max_tokens,
        )

    return NoopLLMClient(f"Unsupported AI provider: {provider_type}")
