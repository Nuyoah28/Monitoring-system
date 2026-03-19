from __future__ import annotations

from typing import Annotated, Callable, Dict, List, Optional, Tuple

from typing_extensions import TypedDict

from langchain.tools import tool
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import InjectedState, ToolNode

from intelligent_agent import (
    IntelligentAgent,
    RequestContext,
    is_non_retryable_spark_error,
)


class AgentGraphState(TypedDict, total=False):
    question: str
    user_token: Optional[str]
    conversation_key: str
    stream_mode: str
    on_chunk: Optional[Callable[[str], None]]
    ctx: RequestContext
    history: List[Dict[str, str]]
    tool_calls: List[Tuple[str, Dict]]
    messages: List[object]
    data_parts: List[str]
    data_summary: str
    final_prompt: str
    answer: str
    skip_primary_ai: bool


class LangGraphIntelligentAgent(IntelligentAgent):
    def __init__(self):
        super().__init__()
        self._tools = self._build_tools()
        self._tool_names = {tool_item.name for tool_item in self._tools}
        self._tool_node = ToolNode(self._tools)
        self._graph = self._build_graph()

    def _build_tools(self):
        @tool("get_alarm_list")
        def get_alarm_list(
            case_types: Optional[List[int]] = None,
            status: Optional[int] = None,
            warning_levels: Optional[List[int]] = None,
            page_size: int = 10,
            time_text: Optional[str] = None,
            state: Annotated[AgentGraphState, InjectedState] = None,
        ) -> str:
            """查询告警列表，支持按类型、状态、等级和时间筛选。"""
            ctx = state["ctx"]
            params = {
                "case_types": case_types or [],
                "status": status,
                "warning_levels": warning_levels or [],
                "page_size": page_size,
                "time_text": time_text,
            }
            return self._execute_tool("get_alarm_list", params, ctx) or ""

        @tool("get_alarm_count")
        def get_alarm_count(
            case_types: Optional[List[int]] = None,
            status: Optional[int] = None,
            warning_levels: Optional[List[int]] = None,
            time_text: Optional[str] = None,
            state: Annotated[AgentGraphState, InjectedState] = None,
        ) -> str:
            """统计符合筛选条件的告警数量。"""
            ctx = state["ctx"]
            params = {
                "case_types": case_types or [],
                "status": status,
                "warning_levels": warning_levels or [],
                "time_text": time_text,
            }
            return self._execute_tool("get_alarm_count", params, ctx) or ""

        @tool("get_alarm_history")
        def get_alarm_history(
            defer: int = 7,
            state: Annotated[AgentGraphState, InjectedState] = None,
        ) -> str:
            """查询近几天的告警趋势统计。"""
            ctx = state["ctx"]
            return self._execute_tool("get_alarm_history", {"defer": defer}, ctx) or ""

        @tool("get_realtime_alarm")
        def get_realtime_alarm(
            state: Annotated[AgentGraphState, InjectedState] = None,
        ) -> str:
            """查询实时告警概况。"""
            ctx = state["ctx"]
            return self._execute_tool("get_realtime_alarm", {}, ctx) or ""

        @tool("get_alarm_detail")
        def get_alarm_detail(
            alarm_id: int,
            state: Annotated[AgentGraphState, InjectedState] = None,
        ) -> str:
            """按告警 ID 查询告警详情。"""
            ctx = state["ctx"]
            return self._execute_tool("get_alarm_detail", {"alarm_id": alarm_id}, ctx) or ""

        @tool("update_alarm_status")
        def update_alarm_status(
            alarm_id: int,
            status: int,
            processing_content: Optional[str] = None,
            state: Annotated[AgentGraphState, InjectedState] = None,
        ) -> str:
            """更新告警处理状态，可标记为已处理或未处理。"""
            ctx = state["ctx"]
            params = {
                "alarm_id": alarm_id,
                "status": status,
                "processing_content": processing_content,
            }
            return self._execute_tool("update_alarm_status", params, ctx) or ""

        @tool("get_monitor_list")
        def get_monitor_list(
            state: Annotated[AgentGraphState, InjectedState] = None,
        ) -> str:
            """查询当前用户可访问的监控点列表。"""
            ctx = state["ctx"]
            return self._execute_tool("get_monitor_list", {}, ctx) or ""

        @tool("get_monitor_detail")
        def get_monitor_detail(
            monitor_id: Optional[int] = None,
            monitor_name: Optional[str] = None,
            state: Annotated[AgentGraphState, InjectedState] = None,
        ) -> str:
            """按监控点 ID 或名称查询监控点详情。"""
            ctx = state["ctx"]
            params = {
                "monitor_id": monitor_id,
                "monitor_name": monitor_name,
            }
            return self._execute_tool("get_monitor_detail", params, ctx) or ""

        @tool("get_weather_newest")
        def get_weather_newest(
            monitor_id: Optional[int] = None,
            monitor_name: Optional[str] = None,
            state: Annotated[AgentGraphState, InjectedState] = None,
        ) -> str:
            """查询指定监控点的最新天气。"""
            ctx = state["ctx"]
            params = {
                "monitor_id": monitor_id,
                "monitor_name": monitor_name,
            }
            return self._execute_tool("get_weather_newest", params, ctx) or ""

        @tool("get_weather_history")
        def get_weather_history(
            monitor_id: Optional[int] = None,
            monitor_name: Optional[str] = None,
            time_text: Optional[str] = None,
            state: Annotated[AgentGraphState, InjectedState] = None,
        ) -> str:
            """查询指定监控点的历史天气，可附带时间范围。"""
            ctx = state["ctx"]
            params = {
                "monitor_id": monitor_id,
                "monitor_name": monitor_name,
                "time_text": time_text,
            }
            return self._execute_tool("get_weather_history", params, ctx) or ""

        @tool("update_detection_prompts")
        def update_detection_prompts(
            prompts: List[str],
            state: Annotated[AgentGraphState, InjectedState] = None,
        ) -> str:
            """更新开放世界检测目标列表。"""
            ctx = state["ctx"]
            return self._execute_tool("update_detection_prompts", {"prompts": prompts}, ctx) or ""

        return [
            get_alarm_list,
            get_alarm_count,
            get_alarm_history,
            get_realtime_alarm,
            get_alarm_detail,
            update_alarm_status,
            get_monitor_list,
            get_monitor_detail,
            get_weather_newest,
            get_weather_history,
            update_detection_prompts,
        ]

    def _build_graph(self):
        graph = StateGraph(AgentGraphState)
        graph.add_node("prepare", self._node_prepare)
        graph.add_node("local_capability", self._node_local_capability)
        graph.add_node("route_tools", self._node_route_tools)
        graph.add_node("llm_plan", self._node_llm_plan)
        graph.add_node("prepare_tool_messages", self._node_prepare_tool_messages)
        graph.add_node("tool_executor", self._tool_node)
        graph.add_node("collect_tool_results", self._node_collect_tool_results)
        graph.add_node("build_prompt", self._node_build_prompt)
        graph.add_node("generate_answer", self._node_generate_answer)
        graph.add_node("persist", self._node_persist)

        graph.add_edge(START, "prepare")
        graph.add_conditional_edges(
            "prepare",
            self._route_after_prepare,
            {
                "local_capability": "local_capability",
                "route_tools": "route_tools",
            },
        )
        graph.add_edge("local_capability", "persist")
        graph.add_conditional_edges(
            "route_tools",
            self._route_after_rule_routing,
            {
                "prepare_tool_messages": "prepare_tool_messages",
                "llm_plan": "llm_plan",
            },
        )
        graph.add_conditional_edges(
            "llm_plan",
            self._route_after_llm_plan,
            {
                "prepare_tool_messages": "prepare_tool_messages",
                "build_prompt": "build_prompt",
            },
        )
        graph.add_edge("prepare_tool_messages", "tool_executor")
        graph.add_edge("tool_executor", "collect_tool_results")
        graph.add_edge("collect_tool_results", "build_prompt")
        graph.add_edge("build_prompt", "generate_answer")
        graph.add_edge("generate_answer", "persist")
        graph.add_edge("persist", END)
        return graph.compile()

    def _normalize_tool_calls(self, tool_calls: List[Tuple[str, Dict]]) -> List[Tuple[str, Dict]]:
        normalized: List[Tuple[str, Dict]] = []
        for tool_name, params in tool_calls:
            if tool_name in self._tool_names:
                normalized.append((tool_name, params if isinstance(params, dict) else {}))
        return normalized

    def _get_tools_desc(self) -> str:
        lines: List[str] = []
        for tool_item in self._tools:
            lines.append(f"- {tool_item.name}: {tool_item.description}")
            for param_name, param_schema in tool_item.args.items():
                schema_type = param_schema.get("type")
                if not schema_type and "anyOf" in param_schema:
                    schema_type = "/".join(
                        choice.get("type", "unknown")
                        for choice in param_schema["anyOf"]
                        if isinstance(choice, dict)
                    )
                lines.append(f"  - {param_name}: {schema_type or 'param'}")
        return "\n".join(lines)

    def _node_prepare(self, state: AgentGraphState) -> AgentGraphState:
        user_token = state.get("user_token")
        conversation_key = state["conversation_key"] or self._default_conversation_key(user_token)
        ctx = RequestContext(user_token=user_token, conversation_key=conversation_key)
        return {
            "conversation_key": conversation_key,
            "ctx": ctx,
            "history": self._get_history(conversation_key),
            "tool_calls": [],
            "messages": [],
            "data_parts": [],
            "data_summary": "",
            "skip_primary_ai": False,
        }

    def _route_after_prepare(self, state: AgentGraphState) -> str:
        if self._is_local_capability_question(state["question"]):
            return "local_capability"
        return "route_tools"

    def _node_local_capability(self, state: AgentGraphState) -> AgentGraphState:
        answer = self._build_local_capability_answer()
        on_chunk = state.get("on_chunk")
        if on_chunk:
            if state.get("stream_mode") == "ws":
                on_chunk("[REPLACE]")
            on_chunk(answer)
        return {"answer": answer}

    def _node_route_tools(self, state: AgentGraphState) -> AgentGraphState:
        question = state["question"]
        ctx = state["ctx"]
        tool_calls = self._rule_based_tool_calls(question, ctx)
        if not tool_calls:
            tool_calls = self._build_contextual_tool_calls(question, ctx)
        return {"tool_calls": self._normalize_tool_calls(tool_calls)}

    def _route_after_rule_routing(self, state: AgentGraphState) -> str:
        if state.get("tool_calls"):
            return "prepare_tool_messages"
        return "llm_plan"

    def _node_llm_plan(self, state: AgentGraphState) -> AgentGraphState:
        try:
            tool_calls = self._normalize_tool_calls(self._llm_tool_calls(state["question"]))
            return {"tool_calls": tool_calls}
        except Exception as exc:
            print(f"工具规划失败，回退为纯知识问答: {exc}")
            return {
                "tool_calls": [],
                "skip_primary_ai": is_non_retryable_spark_error(exc),
            }

    def _route_after_llm_plan(self, state: AgentGraphState) -> str:
        if state.get("tool_calls"):
            return "prepare_tool_messages"
        return "build_prompt"

    def _node_prepare_tool_messages(self, state: AgentGraphState) -> AgentGraphState:
        raw_tool_calls = state.get("tool_calls") or []
        ai_tool_calls = [
            {
                "name": tool_name,
                "args": params,
                "id": f"tool_call_{index}",
                "type": "tool_call",
            }
            for index, (tool_name, params) in enumerate(raw_tool_calls, start=1)
        ]
        return {"messages": [AIMessage(content="", tool_calls=ai_tool_calls)]}

    def _node_collect_tool_results(self, state: AgentGraphState) -> AgentGraphState:
        messages = state.get("messages") or []
        data_parts: List[str] = []
        for message in messages:
            if isinstance(message, ToolMessage):
                content = message.content if isinstance(message.content, str) else str(message.content)
                data_parts.append(f"【{message.name or 'tool'}】\n{content}")
        return {
            "data_parts": data_parts,
            "data_summary": "\n\n".join(data_parts),
            "messages": [],
        }

    def _build_final_prompt(self, question: str, data_summary: str) -> str:
        system_prompt = (
            "你是“智行护卫”监控系统里的智能助手小城，需要结合项目内的真实数据来回答。\n"
            "回答要求：\n"
            "1. 优先使用系统数据，不要编造监控点、告警数量、天气等事实。\n"
            "2. 如果执行了更新类操作，要明确告诉用户已经执行了什么。\n"
            "3. 如果数据不足以回答，要直接说明缺什么，不要假装查到了。\n"
            "4. 回答用中文，风格专业、清晰、简洁，尽量先给结论，再给建议。\n"
            "5. 如果用户在问项目能力，也可以结合本系统支持的监控、告警、天气、开放世界检测等模块回答。"
        )
        if data_summary:
            return (
                f"{system_prompt}\n\n"
                f"用户问题：{question}\n\n"
                f"系统数据：\n{data_summary}\n\n"
                "请基于这些系统数据回答用户，并在必要时给出简短处置建议。"
            )
        return (
            f"{system_prompt}\n\n"
            f"用户问题：{question}\n\n"
            "如果这是知识类问题，请直接回答；"
            "如果是需要系统数据的问题但当前没有查到数据，请明确说明。"
        )

    def _node_build_prompt(self, state: AgentGraphState) -> AgentGraphState:
        return {
            "final_prompt": self._build_final_prompt(
                state["question"],
                state.get("data_summary", ""),
            )
        }

    def _node_generate_answer(self, state: AgentGraphState) -> AgentGraphState:
        on_chunk = state.get("on_chunk")
        stream_mode = state.get("stream_mode", "default")
        data_summary = state.get("data_summary", "")

        if on_chunk and stream_mode == "ws":
            on_chunk("[REPLACE]")

        try:
            answer = self._generate_answer_with_fallback(
                question=state["question"],
                final_prompt=state["final_prompt"],
                history=state.get("history") or [],
                data_summary=data_summary,
                on_chunk=on_chunk,
                user_token=state.get("user_token"),
                conversation_key=state["conversation_key"],
                skip_primary_ai=state.get("skip_primary_ai", False),
            )
        except Exception as exc:
            print(f"AI 响应生成失败: {exc}")
            answer = data_summary or self._build_local_service_fallback(state["question"])
            if on_chunk:
                if stream_mode == "ws" and not data_summary:
                    on_chunk("[REPLACE]")
                on_chunk(answer)
        return {"answer": answer}

    def _node_persist(self, state: AgentGraphState) -> AgentGraphState:
        self._append_history(
            state["conversation_key"],
            state["question"],
            state["answer"],
        )
        return {}

    def process_question(
        self,
        question: str,
        on_chunk: Optional[Callable[[str], None]] = None,
        user_token: Optional[str] = None,
        conversation_key: Optional[str] = None,
        stream_mode: str = "default",
    ) -> str:
        question = (question or "").strip()
        if not question:
            return "问题不能为空。"

        conversation_key = conversation_key or self._default_conversation_key(user_token)
        print(f"\n用户问题: {question}")
        if on_chunk and stream_mode == "ws":
            on_chunk("正在分析您的问题...\n\n")

        result = self._graph.invoke(
            {
                "question": question,
                "user_token": user_token,
                "conversation_key": conversation_key,
                "stream_mode": stream_mode,
                "on_chunk": on_chunk,
            }
        )
        return str(result.get("answer") or "")
