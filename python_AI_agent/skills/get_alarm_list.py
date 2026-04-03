from __future__ import annotations

from skills.base import AgentSkill, SkillRuntime


class GetAlarmListSkill(AgentSkill):
    name = "get_alarm_list"
    description = "查询告警列表，支持类型、状态、等级和时间筛选。"
    parameters = {
        "case_types": "可选，int 数组，例如 [5] 表示明火",
        "status": "可选，0=未处理，1=已处理",
        "warning_levels": "可选，int 数组，例如 [4, 5]",
        "page_size": "可选，返回条数，默认 10",
        "time_text": "可选，自然语言时间，如 今天、近7天",
    }

    def run(self, params: dict, runtime: SkillRuntime) -> str:
        return runtime.support.handle_get_alarm_list(runtime.request_context, params)


def build_skill() -> AgentSkill:
    return GetAlarmListSkill()
