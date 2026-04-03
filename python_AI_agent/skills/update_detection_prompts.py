from __future__ import annotations

from skills.base import AgentSkill, SkillRuntime


class UpdateDetectionPromptsSkill(AgentSkill):
    name = "update_detection_prompts"
    description = "更新开放世界检测目标列表。"
    parameters = {
        "prompts": "必填，字符串数组，例如 ['红色电动车', '戴帽子的人']",
    }

    def run(self, params: dict, runtime: SkillRuntime) -> str:
        return runtime.support.handle_update_detection_prompts(runtime.request_context, params)


def build_skill() -> AgentSkill:
    return UpdateDetectionPromptsSkill()
