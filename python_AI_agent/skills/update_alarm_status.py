from __future__ import annotations

from skills.base import AgentSkill, SkillRuntime


class UpdateAlarmStatusSkill(AgentSkill):
    name = "update_alarm_status"
    description = "更新告警处理状态，可标记为已处理或未处理。"
    parameters = {
        "alarm_id": "必填，告警 ID",
        "status": "必填，0=未处理，1=已处理",
        "processing_content": "可选，处理说明",
    }

    def run(self, params: dict, runtime: SkillRuntime) -> str:
        return runtime.support.handle_update_alarm_status(runtime.request_context, params)


def build_skill() -> AgentSkill:
    return UpdateAlarmStatusSkill()
