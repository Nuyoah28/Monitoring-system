from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any


class FlowReporter:
    def __init__(self, output_jsonl: str | None = None, http_config: dict[str, Any] | None = None) -> None:
        self.output_path = Path(output_jsonl).expanduser().resolve() if output_jsonl else None
        self.http_config = http_config or {}

    def emit(self, payload: dict[str, Any]) -> None:
        if self.output_path:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            with self.output_path.open("a", encoding="utf-8") as file:
                file.write(json.dumps(payload, ensure_ascii=False) + "\n")

        url = self.http_config.get("url")
        if url:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            request = urllib.request.Request(url=url, data=body, method="POST")
            request.add_header("Content-Type", "application/json")
            for key, value in self.http_config.get("headers", {}).items():
                request.add_header(key, value)
            timeout = float(self.http_config.get("timeout_seconds", 5))
            with urllib.request.urlopen(request, timeout=timeout) as response:
                response.read()

