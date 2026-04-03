from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

from skills.base import AgentSkill


class SkillRegistry:
    def __init__(self, skills: list[AgentSkill]):
        self._skills = {skill.name: skill for skill in skills}

    @classmethod
    def discover(cls) -> "SkillRegistry":
        package_path = Path(__file__).resolve().parent
        skills: list[AgentSkill] = []
        for module_info in sorted(pkgutil.iter_modules([str(package_path)]), key=lambda item: item.name):
            if module_info.name in {"base", "registry", "__init__"}:
                continue
            module = importlib.import_module(f"skills.{module_info.name}")
            builder = getattr(module, "build_skill", None)
            if not callable(builder):
                continue
            skill = builder()
            if isinstance(skill, AgentSkill):
                skills.append(skill)
        return cls(skills)

    def get(self, name: str) -> AgentSkill | None:
        return self._skills.get(name)

    def describe(self) -> str:
        lines: list[str] = []
        for skill in self.list():
            lines.append(f"- {skill.name}: {skill.description}")
            for param_name, param_desc in skill.parameters.items():
                lines.append(f"  - {param_name}: {param_desc}")
        return "\n".join(lines)

    def list(self) -> list[AgentSkill]:
        return [self._skills[name] for name in sorted(self._skills)]
