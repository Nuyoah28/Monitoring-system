from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _int_value(value: Any, env_name: str, default: int) -> int:
    if value in (None, ""):
        return _int_env(env_name, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return _int_env(env_name, default)


def _dict_value(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string_value(value: Any, env_name: str, default: str) -> str:
    if value in (None, ""):
        return str(os.getenv(env_name, default))
    return str(value)


@dataclass(frozen=True)
class AgentSettings:
    config_path: str
    backend_base_url: str
    backend_username: str
    backend_password: str
    spark_app_id: str
    spark_api_key: str
    spark_api_secret: str
    spark_host_url: str
    openai_base_url: str
    openai_api_key: str
    openai_model: str
    ai_active_provider: str
    ai_providers: dict[str, dict[str, Any]]
    max_history_messages: int
    max_alarm_fetch_pages: int
    alarm_page_size: int
    memory_ttl_seconds: int
    max_agent_workers: int


_DEFAULT_CONFIG_PATH = str(
    (Path(__file__).resolve().parent.parent / "agent_config.json")
)


def _load_agent_config(config_path: str) -> dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


_CONFIG_PATH = (
    os.getenv("AGENT_CONFIG_PATH")
    or os.getenv("AGENT_AI_CONFIG_PATH")
    or _DEFAULT_CONFIG_PATH
)
_FILE_CONFIG = _load_agent_config(_CONFIG_PATH)
_BACKEND_CONFIG = _dict_value(_FILE_CONFIG.get("backend"))
_RUNTIME_CONFIG = _dict_value(_FILE_CONFIG.get("runtime"))
_AI_CONFIG = _dict_value(_FILE_CONFIG.get("ai"))

if not _AI_CONFIG and {"active_provider", "providers"} <= set(_FILE_CONFIG.keys()):
    _AI_CONFIG = {
        "active_provider": _FILE_CONFIG.get("active_provider"),
        "providers": _FILE_CONFIG.get("providers"),
    }


SETTINGS = AgentSettings(
    config_path=_CONFIG_PATH,
    backend_base_url=_string_value(
        _BACKEND_CONFIG.get("base_url"),
        "AGENT_BACKEND_BASE_URL",
        "http://localhost:10215/api/v1",
    ).rstrip("/"),
    backend_username=_string_value(_BACKEND_CONFIG.get("username"), "AGENT_BACKEND_USERNAME", "root"),
    backend_password=_string_value(_BACKEND_CONFIG.get("password"), "AGENT_BACKEND_PASSWORD", "123456"),
    spark_app_id=_string_value(_dict_value(_AI_CONFIG.get("providers")).get("spark", {}).get("app_id"), "XF_APPID", ""),
    spark_api_key=_string_value(_dict_value(_AI_CONFIG.get("providers")).get("spark", {}).get("api_key"), "XF_API_KEY", ""),
    spark_api_secret=_string_value(
        _dict_value(_AI_CONFIG.get("providers")).get("spark", {}).get("api_secret"),
        "XF_API_SECRET",
        "",
    ),
    spark_host_url=_string_value(
        _dict_value(_AI_CONFIG.get("providers")).get("spark", {}).get("host_url"),
        "XF_HOST_URL",
        "https://spark-api.xf-yun.com/v1/x1",
    ),
    openai_base_url=_string_value(
        _dict_value(_AI_CONFIG.get("providers")).get("openai_compatible", {}).get("base_url"),
        "OPENAI_BASE_URL",
        "",
    ),
    openai_api_key=_string_value(
        _dict_value(_AI_CONFIG.get("providers")).get("openai_compatible", {}).get("api_key"),
        "OPENAI_API_KEY",
        "",
    ),
    openai_model=_string_value(
        _dict_value(_AI_CONFIG.get("providers")).get("openai_compatible", {}).get("model"),
        "OPENAI_MODEL",
        "",
    ),
    ai_active_provider=str(_AI_CONFIG.get("active_provider") or "disabled"),
    ai_providers={
        str(name): provider
        for name, provider in _dict_value(_AI_CONFIG.get("providers")).items()
        if isinstance(provider, dict)
    },
    max_history_messages=_int_value(_RUNTIME_CONFIG.get("max_history_messages"), "AGENT_MAX_HISTORY_MESSAGES", 6),
    max_alarm_fetch_pages=_int_value(_RUNTIME_CONFIG.get("max_alarm_fetch_pages"), "AGENT_MAX_ALARM_FETCH_PAGES", 30),
    alarm_page_size=_int_value(_RUNTIME_CONFIG.get("alarm_page_size"), "AGENT_ALARM_PAGE_SIZE", 100),
    memory_ttl_seconds=_int_value(_RUNTIME_CONFIG.get("memory_ttl_seconds"), "AGENT_MEMORY_TTL_SECONDS", 7200),
    max_agent_workers=max(4, _int_value(_RUNTIME_CONFIG.get("max_agent_workers"), "AGENT_MAX_WORKERS", 16)),
)
