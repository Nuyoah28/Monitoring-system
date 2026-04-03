from __future__ import annotations

from skills.base import AgentSkill, SkillRuntime


class GetRealtimeAlarmSkill(AgentSkill):
    name = "get_realtime_alarm"
    description = "查询实时告警概况和大屏态势数据。"
    parameters = {}

    def run(self, params: dict, runtime: SkillRuntime) -> str:
        return runtime.support.handle_get_realtime_alarm(runtime.request_context, params)


def build_skill() -> AgentSkill:
    return GetRealtimeAlarmSkill()
