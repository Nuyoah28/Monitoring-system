from __future__ import annotations

from skills.base import AgentSkill, SkillRuntime


class GetAlarmDetailSkill(AgentSkill):
    name = "get_alarm_detail"
    description = "按告警 ID 查询告警详情。"
    parameters = {
        "alarm_id": "必填，告警 ID",
    }

    def run(self, params: dict, runtime: SkillRuntime) -> str:
        return runtime.support.handle_get_alarm_detail(runtime.request_context, params)


def build_skill() -> AgentSkill:
    return GetAlarmDetailSkill()
