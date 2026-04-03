from __future__ import annotations

from skills.base import AgentSkill, SkillRuntime


class GetWeatherHistorySkill(AgentSkill):
    name = "get_weather_history"
    description = "查询指定监控点的历史天气记录。"
    parameters = {
        "monitor_id": "可选，监控点 ID",
        "monitor_name": "可选，监控点名称",
        "time_text": "可选，自然语言时间，如 昨天、近7天",
    }

    def run(self, params: dict, runtime: SkillRuntime) -> str:
        return runtime.support.handle_get_weather_history(runtime.request_context, params)


def build_skill() -> AgentSkill:
    return GetWeatherHistorySkill()
