from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from agent_core.backend_client import BackendClient
from agent_core.config.settings import SETTINGS, AgentSettings
from agent_core.core.catalog import ToolCatalog
from agent_core.core.context import RequestContext
from agent_core.core.planner import ToolPlanner
from agent_core.core.session_logger import SessionLogger
from agent_core.llm_client import create_llm_client
from agent_core.memory.store import ConversationMemoryStore
from agent_core.prompts import (
    build_data_fallback_answer,
    build_final_answer_prompt,
    build_local_capability_answer,
    build_local_service_fallback,
    is_local_capability_question,
)
from agent_core.skill_support import SkillSupport
from agent_core.tools.gateway import ToolGateway
from agent_core.utils import build_conversation_key


class ReactIntelligentAgent:
    def __init__(self, settings: AgentSettings = SETTINGS):
        self.settings = settings
        self.backend = BackendClient(
            base_url=settings.backend_base_url,
            username=settings.backend_username,
            password=settings.backend_password,
        )
        self.tools = ToolGateway(self.backend)
        self.ai_client = create_llm_client(settings)
        self.memory_store = ConversationMemoryStore(
            history_limit=settings.max_history_messages,
            ttl_seconds=settings.memory_ttl_seconds,
            db_path=settings.memory_db_path,
        )
        self.support = SkillSupport(self.tools, self.memory_store, settings)
        self.session_logger = SessionLogger(settings.log_dir)

        skills_dir = Path(__file__).resolve().parent.parent.parent / "skills"
        self.tool_catalog = ToolCatalog.discover(skills_dir)
        self.planner = ToolPlanner(self.ai_client, self.tool_catalog, self.support)

    def _default_conversation_key(self, user_token: Optional[str]) -> str:
        return build_conversation_key(user_token)

    def _get_history(self, conversation_key: str) -> list[dict[str, str]]:
        return self.memory_store.get_history(
            conversation_key,
            top_k=self.settings.memory_vector_top_k,
        )

    def _append_history(self, conversation_key: str, question: str, answer: str) -> None:
        self.memory_store.append_turn(conversation_key, question, answer)

    def _execute_tool_calls(
        self,
        tool_calls: list[tuple[str, dict]],
        request_context: RequestContext,
        on_event: Optional[Callable[[str, str], None]] = None,
    ) -> list[str]:
        observations: list[str] = []
        for tool_name, params in tool_calls:
            tool_spec = self.tool_catalog.get(tool_name)
            if tool_spec is None:
                continue
            try:
                if on_event:
                    on_event("using_tools", f"using tool `{tool_name}` from {tool_spec.source_file}")
                self.session_logger.log(
                    request_context.conversation_key,
                    "tool_call",
                    {
                        "tool": tool_name,
                        "params": params or {},
                        "source": tool_spec.source_file,
                    },
                )
                result = self.tools.execute(tool_name, params or {}, self.support, request_context)
                if result:
                    observations.append(result)
                self.session_logger.log(
                    request_context.conversation_key,
                    "tool_result",
                    {
                        "tool": tool_name,
                        "result": result,
                    },
                )
            except Exception as exc:
                print(f"Tool execution failed: {tool_name}: {exc}")
                observations.append("相关系统查询失败，请稍后重试。")
                self.session_logger.log(
                    request_context.conversation_key,
                    "tool_error",
                    {
                        "tool": tool_name,
                        "error": str(exc),
                    },
                )
        return observations

    def _generate_answer_with_fallback(
        self,
        *,
        question: str,
        final_prompt: str,
        history: list[dict[str, str]],
        data_summary: str,
        on_chunk: Optional[Callable[[str], None]] = None,
        user_token: Optional[str] = None,
        conversation_key: Optional[str] = None,
        skip_primary_ai: bool = False,
        stream_mode: str = "default",
    ) -> str:
        stream_has_started = False

        def emit(text: str) -> None:
            nonlocal stream_has_started
            if not on_chunk:
                return
            if stream_mode == "ws" and not stream_has_started:
                on_chunk("[REPLACE]")
            stream_has_started = True
            on_chunk(text)

        skip_primary_ai = skip_primary_ai or not getattr(self.ai_client, "is_available", True)
        if not skip_primary_ai:
            try:
                return self.ai_client.chat(
                    final_prompt,
                    context=history,
                    on_chunk=emit if on_chunk else None,
                )
            except Exception as exc:
                print(f"AI answer generation failed: {exc}")

        if data_summary:
            fallback = build_data_fallback_answer(question, data_summary)
            emit(fallback)
            return fallback

        try:
            cbs_answer = self.tools.chat_cbs(
                question,
                user_token=user_token,
                conversation_key=conversation_key,
            )
            if cbs_answer:
                emit(cbs_answer)
                return cbs_answer
        except Exception as exc:
            print(f"CBS answer generation failed: {exc}")

        fallback = build_local_service_fallback(question)
        emit(fallback)
        return fallback

    def process_question(
        self,
        question: str,
        on_chunk: Optional[Callable[[str], None]] = None,
        on_event: Optional[Callable[[str, str], None]] = None,
        user_token: Optional[str] = None,
        conversation_key: Optional[str] = None,
        stream_mode: str = "default",
        current_time: Optional[datetime] = None,
    ) -> str:
        question = (question or "").strip()
        if not question:
            return "问题不能为空。"

        conversation_key = conversation_key or self._default_conversation_key(user_token)
        current_time = current_time or datetime.now()
        request_context = RequestContext(
            user_token=user_token,
            conversation_key=conversation_key,
            current_time=current_time,
        )

        if on_event:
            on_event("reading", "reading question and loading context")

        self.session_logger.log(
            conversation_key,
            "question",
            {
                "question": question,
                "user_token_present": bool(user_token),
            },
        )

        print(f"\n用户问题: {question}")
        if on_chunk and stream_mode == "ws":
            on_chunk("正在分析您的问题...\n\n")

        if is_local_capability_question(question):
            answer = build_local_capability_answer()
            if on_chunk:
                if stream_mode == "ws":
                    on_chunk("[REPLACE]")
                on_chunk(answer)
            self._append_history(conversation_key, question, answer)
            if on_event:
                on_event("done", "done")
            return answer

        if on_event:
            on_event("searching_skills", "searching skill catalog")

        tool_calls, skip_primary_ai = self.planner.plan(question, request_context)
        if on_event:
            if tool_calls:
                on_event("planning", "planning complete, model selected tools")
            else:
                on_event("planning", "no tool selected, answer directly")
        observations = self._execute_tool_calls(tool_calls, request_context, on_event=on_event)
        data_summary = "\n\n".join(observations)
        final_prompt = build_final_answer_prompt(
            question,
            data_summary,
            current_time.strftime("%Y-%m-%d %H:%M:%S"),
        )
        history = self.memory_store.get_history(
            conversation_key,
            query=question,
            top_k=self.settings.memory_vector_top_k,
        )

        if on_event:
            on_event("thinking", "generating final answer")

        answer = self._generate_answer_with_fallback(
            question=question,
            final_prompt=final_prompt,
            history=history,
            data_summary=data_summary,
            on_chunk=on_chunk,
            user_token=user_token,
            conversation_key=conversation_key,
            skip_primary_ai=skip_primary_ai,
            stream_mode=stream_mode,
        )
        self._append_history(conversation_key, question, answer)
        self.session_logger.log(
            conversation_key,
            "answer",
            {
                "answer": answer,
                "tool_calls": [name for name, _ in tool_calls],
                "observation_count": len(observations),
            },
        )
        if on_event:
            on_event("done", "done")
        return answer

    def chat(
        self,
        question: str,
        on_chunk: Optional[Callable[[str], None]] = None,
        on_event: Optional[Callable[[str, str], None]] = None,
        user_token: Optional[str] = None,
        conversation_key: Optional[str] = None,
        stream_mode: str = "default",
    ) -> str:
        return self.process_question(
            question=question,
            on_chunk=on_chunk,
            on_event=on_event,
            user_token=user_token,
            conversation_key=conversation_key,
            stream_mode=stream_mode,
        )
