from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, str]
    context_preview: str
    source_file: str


class ToolCatalog:
    def __init__(self, tools: list[ToolSpec]):
        self._tools = {tool.name: tool for tool in tools}

    @classmethod
    def discover(cls, skills_dir: Path) -> "ToolCatalog":
        tools: list[ToolSpec] = []
        for md_path in sorted(skills_dir.glob("*.md")):
            tools.extend(_parse_tools_from_markdown(md_path))
        return cls(tools)

    def get(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    def list(self) -> list[ToolSpec]:
        return [self._tools[name] for name in sorted(self._tools)]

    def describe(self) -> str:
        lines: list[str] = []
        for tool in self.list():
            lines.append(f"- {tool.name}: {tool.description}")
            for key, value in tool.parameters.items():
                lines.append(f"  - {key}: {value}")
            if tool.context_preview:
                lines.append("  - context_preview:")
                for preview_line in tool.context_preview.splitlines():
                    lines.append(f"    {preview_line}")
        return "\n".join(lines)


def _parse_tools_from_markdown(md_path: Path) -> list[ToolSpec]:
    lines = md_path.read_text(encoding="utf-8").splitlines()
    context_preview = "\n".join(lines[:10]).strip()

    tools: list[ToolSpec] = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        tool_match = re.match(r"^###\s+\d+\.\s+([a-zA-Z0-9_]+)\s*-\s*(.+)$", line)
        if not tool_match:
            i += 1
            continue

        tool_name = tool_match.group(1).strip()
        fallback_desc = tool_match.group(2).strip()
        desc = fallback_desc
        params: dict[str, str] = {}

        j = i + 1
        while j < len(lines):
            current = lines[j].rstrip()
            stripped = current.strip()
            if stripped.startswith("### "):
                break

            feature_match = re.match(r"^-\s*\*\*功能\*\*\s*:\s*(.+)$", stripped)
            if feature_match:
                desc = feature_match.group(1).strip()

            param_match = re.match(r"^[-*]\s*`([^`]+)`\s*:\s*(.+)$", stripped)
            if param_match:
                params[param_match.group(1).strip()] = param_match.group(2).strip()

            j += 1

        tools.append(
            ToolSpec(
                name=tool_name,
                description=desc,
                parameters=params,
                context_preview=context_preview,
                source_file=md_path.name,
            )
        )
        i = j

    return tools
