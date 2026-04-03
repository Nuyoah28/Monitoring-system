from __future__ import annotations

from skills.base import AgentSkill, SkillRuntime


class GetWeatherNewestSkill(AgentSkill):
    name = "get_weather_newest"
    description = "查询指定监控点的最新天气。"
    parameters = {
        "monitor_id": "可选，监控点 ID",
        "monitor_name": "可选，监控点名称",
    }

    def run(self, params: dict, runtime: SkillRuntime) -> str:
        return runtime.support.handle_get_weather_newest(runtime.request_context, params)


def build_skill() -> AgentSkill:
    return GetWeatherNewestSkill()
