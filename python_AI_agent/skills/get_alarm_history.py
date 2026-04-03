from __future__ import annotations

from skills.base import AgentSkill, SkillRuntime


class GetAlarmHistorySkill(AgentSkill):
    name = "get_alarm_history"
    description = "查询告警趋势和历史变化。"
    parameters = {
        "defer": "可选，1/3/7/30，分别表示今天、近3天、近7天、近30天",
    }

    def run(self, params: dict, runtime: SkillRuntime) -> str:
        return runtime.support.handle_get_alarm_history(runtime.request_context, params)


def build_skill() -> AgentSkill:
    return GetAlarmHistorySkill()
