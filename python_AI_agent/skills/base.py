from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent_core.context import RequestContext


@dataclass
class SkillRuntime:
    request_context: RequestContext
    backend: Any
    support: Any


class AgentSkill:
    name: str = ""
    description: str = ""
    parameters: dict[str, str] = {}

    def run(self, params: dict[str, Any], runtime: SkillRuntime) -> str:
        raise NotImplementedError
