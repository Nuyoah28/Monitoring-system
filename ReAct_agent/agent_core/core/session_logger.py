from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Optional


class SessionLogger:
    def __init__(self, log_dir: str):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    @staticmethod
    def _now() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _safe_name(name: str) -> str:
        return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in name)

    @staticmethod
    def _truncate(value: Any, max_len: int = 1200) -> Any:
        if isinstance(value, str):
            if len(value) <= max_len:
                return value
            return value[:max_len] + " ...[truncated]"
        if isinstance(value, list):
            return [SessionLogger._truncate(item, max_len=max_len) for item in value[:20]]
        if isinstance(value, dict):
            result: dict[str, Any] = {}
            for index, (key, val) in enumerate(value.items()):
                if index >= 30:
                    result["..."] = "[truncated keys]"
                    break
                result[str(key)] = SessionLogger._truncate(val, max_len=max_len)
            return result
        return value

    def _resolve_file(self, conversation_key: Optional[str]) -> Path:
        if conversation_key:
            file_name = f"session_{self._safe_name(conversation_key)}.log"
            return self.log_dir / file_name
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return self.log_dir / f"session_{ts}.log"

    def log(self, conversation_key: Optional[str], event: str, payload: dict[str, Any]) -> None:
        path = self._resolve_file(conversation_key)
        compact_payload = self._truncate(payload)
        lines: list[str] = [
            f"[{self._now()}] event={event}",
        ]
        for key, value in compact_payload.items():
            pretty = json.dumps(value, ensure_ascii=False, indent=2)
            indented = "\n".join(f"    {line}" for line in pretty.splitlines())
            lines.append(f"  {key}:")
            lines.append(indented)
        lines.append("")

        with self._lock:
            with path.open("a", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
