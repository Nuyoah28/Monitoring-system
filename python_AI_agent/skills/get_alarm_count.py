from __future__ import annotations

from skills.base import AgentSkill, SkillRuntime


class GetAlarmCountSkill(AgentSkill):
    name = "get_alarm_count"
    description = "统计符合筛选条件的告警数量。"
    parameters = {
        "case_types": "可选，int 数组，例如 [5]",
        "status": "可选，0=未处理，1=已处理",
        "warning_levels": "可选，int 数组，例如 [4, 5]",
        "time_text": "可选，自然语言时间，如 今天、近7天",
    }

    def run(self, params: dict, runtime: SkillRuntime) -> str:
        return runtime.support.handle_get_alarm_count(runtime.request_context, params)


def build_skill() -> AgentSkill:
    return GetAlarmCountSkill()
