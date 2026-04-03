from __future__ import annotations

from skills.base import AgentSkill, SkillRuntime


class GetMonitorListSkill(AgentSkill):
    name = "get_monitor_list"
    description = "查询当前用户可访问的监控点列表。"
    parameters = {}

    def run(self, params: dict, runtime: SkillRuntime) -> str:
        return runtime.support.handle_get_monitor_list(runtime.request_context, params)


def build_skill() -> AgentSkill:
    return GetMonitorListSkill()
