from __future__ import annotations

from agent_core.constants import LOCAL_CAPABILITY_KEYWORDS
from agent_core.utils import contains_any


ANSWER_SYSTEM_PROMPT = """你是“社区智眼”监控系统里的智能助手，需要结合系统真实数据回答用户。

回答要求：
1. 优先使用系统数据，不要编造监控点、告警数量、天气等事实。
2. 如果执行了更新类操作，要明确告诉用户做了什么。
3. 如果数据不足以回答，就直接说明缺什么，不要假装查到了。
4. 回答用中文，风格专业、清晰、简洁，尽量先给结论，再给建议。
5. 如果用户在问系统能力，可以结合监控、告警、天气、检测目标下发等模块来回答。
6. 涉及“今天、昨天、本周、本月、当前时间”等时间问题时，以本次请求上下文里的当前时间为准，不要使用模型训练时间。"""

WEB_FAILURE_HINT = """
如果工具结果中出现“联网访问失败”“403”“反爬”“Jina 代理”等描述，
不要说“超出系统范围”或“系统不支持网页任务”。
应明确说明：这是外部站点访问限制导致抓取失败，建议改用浏览器/CDP模式或更换访问方式。
"""

TOOL_SELECTION_TEMPLATE = """你是监控系统的工具规划助手。请根据用户问题，只输出 JSON，不要输出其他解释。

当前时间：{current_time}

输出规则：
1. 只需要一个工具时：{{"tool":"工具名","params":{{...}}}}
2. 需要多个工具时：[{{"tool":"工具名","params":{{...}}}}, {{"tool":"工具名","params":{{...}}}}]
3. 不需要调用工具时：{{"tool":"none","params":{{}}}}

约束：
- 告警类型请用 case_types 数组，值来自 1~12。
- 告警状态请用 status，0 表示未处理，1 表示已处理。
- 告警等级请用 warning_levels 数组。
- 监控点优先传 monitor_name，只有明确给出数字 ID 时才传 monitor_id。
- 如果用户明确要求设置检测目标，请调用 update_detection_prompts。
- 如果用户明确要求修改告警处理状态，请调用 update_alarm_status。
- 如果用户要求联网搜索、网页访问或URL抓取，优先调用 web_access。

工具列表：
{skills_desc}

用户问题：
{question}

JSON："""


def build_tool_selection_prompt(skills_desc: str, question: str, current_time: str) -> str:
    return TOOL_SELECTION_TEMPLATE.format(
        skills_desc=skills_desc,
        question=question,
        current_time=current_time,
    )


def build_final_answer_prompt(question: str, data_summary: str, current_time: str) -> str:
    if data_summary:
        return (
            f"{ANSWER_SYSTEM_PROMPT}\n\n"
            f"{WEB_FAILURE_HINT}\n\n"
            f"当前时间：{current_time}\n\n"
            f"用户问题：{question}\n\n"
            f"系统数据：\n{data_summary}\n\n"
            "请基于这些系统数据回答用户，并在必要时给出简短处置建议。"
        )
    return (
        f"{ANSWER_SYSTEM_PROMPT}\n\n"
        f"当前时间：{current_time}\n\n"
        f"用户问题：{question}\n\n"
        "如果这是知识类问题，请直接回答；"
        "如果这是需要系统数据的问题但当前没有查到数据，请明确说明。"
    )


def is_local_capability_question(question: str) -> bool:
    normalized = (question or "").lower()
    return contains_any(normalized, [keyword.lower() for keyword in LOCAL_CAPABILITY_KEYWORDS])


def build_local_capability_answer() -> str:
    return (
        "我是“社区智眼”监控系统的智能助手。"
        "目前可以帮你查询告警列表、统计未处理告警、查看告警详情、"
        "查询监控点信息、查询最新或历史天气、更新告警处理状态，"
        "以及下发开放世界检测目标。"
        "你可以直接说：“今天有多少条未处理告警”、“查看告警 12 详情”"
        "或“把告警 12 标记为已处理”。"
    )


def build_data_fallback_answer(question: str, data_summary: str) -> str:
    lines = [
        "根据当前系统数据，结果如下：",
        data_summary,
    ]
    if contains_any(question, ["建议", "怎么处理", "如何处理", "怎么办"]):
        lines.append("建议优先处理高等级、未处理告警，并复核对应监控点视频和现场情况。")
    return "\n\n".join(lines)


def build_local_service_fallback(question: str) -> str:
    if contains_any(question, ["能力", "你能做什么", "支持什么", "介绍一下"]):
        return (
            "当前智能生成服务暂时不稳定，但系统仍支持这些能力："
            "查询告警列表、统计实时告警、查看告警详情、查询监控点信息、"
            "查询天气、更新告警状态和下发检测目标。"
        )
    return (
        "当前外部 AI 应答服务暂时不稳定，但监控系统数据查询仍可以继续使用。"
        "你可以直接试试：“今天有多少条未处理告警”、“查看告警 12 详情”、"
        "“1 号监控点最新天气”或“把告警 12 标记为已处理”。"
    )
