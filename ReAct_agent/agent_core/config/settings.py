from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _load_dotenv_values(dotenv_path: Path) -> dict[str, str]:
    if not dotenv_path.exists():
        return {}

    result: dict[str, str] = {}
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            result[key] = value
    return result


def _dict_value(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _load_agent_config(config_path: str) -> dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _resolve_value(
    dotenv_values: dict[str, str],
    env_name: str,
    file_value: Any,
    default: Any,
) -> Any:
    if env_name in dotenv_values and dotenv_values[env_name] not in ("", None):
        return dotenv_values[env_name]
    env_value = os.getenv(env_name)
    if env_value not in (None, ""):
        return env_value
    if file_value not in (None, ""):
        return file_value
    return default


def _resolve_int(
    dotenv_values: dict[str, str],
    env_name: str,
    file_value: Any,
    default: int,
) -> int:
    value = _resolve_value(dotenv_values, env_name, file_value, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class AgentSettings:
    config_path: str
    dotenv_path: str
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
    memory_vector_top_k: int
    max_agent_workers: int


def load_settings() -> AgentSettings:
    base_dir = Path(__file__).resolve().parent.parent.parent
    default_config_path = str(base_dir / "agent_config.json")
    default_dotenv_path = str(base_dir / ".env")

    config_path = os.getenv("AGENT_CONFIG_PATH") or os.getenv("AGENT_AI_CONFIG_PATH") or default_config_path
    dotenv_path = os.getenv("AGENT_DOTENV_PATH") or default_dotenv_path

    dotenv_values = _load_dotenv_values(Path(dotenv_path))
    file_config = _load_agent_config(config_path)

    backend_config = _dict_value(file_config.get("backend"))
    runtime_config = _dict_value(file_config.get("runtime"))
    ai_config = _dict_value(file_config.get("ai"))

    if not ai_config and {"active_provider", "providers"} <= set(file_config.keys()):
        ai_config = {
            "active_provider": file_config.get("active_provider"),
            "providers": file_config.get("providers"),
        }

    providers = {
        str(name): provider
        for name, provider in _dict_value(ai_config.get("providers")).items()
        if isinstance(provider, dict)
    }
    spark_provider = _dict_value(providers.get("spark"))
    openai_provider = _dict_value(providers.get("openai_compatible"))

    return AgentSettings(
        config_path=config_path,
        dotenv_path=dotenv_path,
        backend_base_url=str(
            _resolve_value(
                dotenv_values,
                "AGENT_BACKEND_BASE_URL",
                backend_config.get("base_url"),
                "http://localhost:10215/api/v1",
            )
        ).rstrip("/"),
        backend_username=str(_resolve_value(dotenv_values, "AGENT_BACKEND_USERNAME", backend_config.get("username"), "root")),
        backend_password=str(_resolve_value(dotenv_values, "AGENT_BACKEND_PASSWORD", backend_config.get("password"), "123456")),
        spark_app_id=str(_resolve_value(dotenv_values, "XF_APPID", spark_provider.get("app_id"), "")),
        spark_api_key=str(_resolve_value(dotenv_values, "XF_API_KEY", spark_provider.get("api_key"), "")),
        spark_api_secret=str(_resolve_value(dotenv_values, "XF_API_SECRET", spark_provider.get("api_secret"), "")),
        spark_host_url=str(
            _resolve_value(
                dotenv_values,
                "XF_HOST_URL",
                spark_provider.get("host_url"),
                "https://spark-api.xf-yun.com/v1/x1",
            )
        ),
        openai_base_url=str(_resolve_value(dotenv_values, "OPENAI_BASE_URL", openai_provider.get("base_url"), "")),
        openai_api_key=str(_resolve_value(dotenv_values, "OPENAI_API_KEY", openai_provider.get("api_key"), "")),
        openai_model=str(_resolve_value(dotenv_values, "OPENAI_MODEL", openai_provider.get("model"), "")),
        ai_active_provider=str(_resolve_value(dotenv_values, "AGENT_ACTIVE_PROVIDER", ai_config.get("active_provider"), "disabled")),
        ai_providers=providers,
        max_history_messages=_resolve_int(dotenv_values, "AGENT_MAX_HISTORY_MESSAGES", runtime_config.get("max_history_messages"), 6),
        max_alarm_fetch_pages=_resolve_int(dotenv_values, "AGENT_MAX_ALARM_FETCH_PAGES", runtime_config.get("max_alarm_fetch_pages"), 30),
        alarm_page_size=_resolve_int(dotenv_values, "AGENT_ALARM_PAGE_SIZE", runtime_config.get("alarm_page_size"), 100),
        memory_ttl_seconds=_resolve_int(dotenv_values, "AGENT_MEMORY_TTL_SECONDS", runtime_config.get("memory_ttl_seconds"), 7200),
        memory_vector_top_k=max(1, _resolve_int(dotenv_values, "AGENT_MEMORY_VECTOR_TOP_K", runtime_config.get("memory_vector_top_k"), 4)),
        max_agent_workers=max(4, _resolve_int(dotenv_values, "AGENT_MAX_WORKERS", runtime_config.get("max_agent_workers"), 16)),
    )


SETTINGS = load_settings()
