from __future__ import annotations

from skills.base import AgentSkill, SkillRuntime


class GetMonitorDetailSkill(AgentSkill):
    name = "get_monitor_detail"
    description = "按监控点 ID 或名称查询监控点详情。"
    parameters = {
        "monitor_id": "可选，监控点 ID",
        "monitor_name": "可选，监控点名称",
    }

    def run(self, params: dict, runtime: SkillRuntime) -> str:
        return runtime.support.handle_get_monitor_detail(runtime.request_context, params)


def build_skill() -> AgentSkill:
    return GetMonitorDetailSkill()
