from __future__ import annotations

from typing import Callable, Optional

from agent_core.backend_client import BackendClient
from agent_core.config import SETTINGS, AgentSettings
from agent_core.context import RequestContext
from agent_core.llm_client import create_llm_client
from agent_core.memory import ConversationMemoryStore
from agent_core.planner import SkillPlanner
from agent_core.prompts import (
    build_data_fallback_answer,
    build_final_answer_prompt,
    build_local_capability_answer,
    build_local_service_fallback,
    is_local_capability_question,
)
from agent_core.skill_support import SkillSupport
from agent_core.utils import build_conversation_key
from skills import SkillRegistry, SkillRuntime


class ReactIntelligentAgent:
    def __init__(self, settings: AgentSettings = SETTINGS):
        self.settings = settings
        self.backend = BackendClient(
            base_url=settings.backend_base_url,
            username=settings.backend_username,
            password=settings.backend_password,
        )
        self.ai_client = create_llm_client(settings)
        self.memory_store = ConversationMemoryStore(
            history_limit=settings.max_history_messages,
            ttl_seconds=settings.memory_ttl_seconds,
        )
        self.support = SkillSupport(self.backend, self.memory_store, settings)
        self.skill_registry = SkillRegistry.discover()
        self.planner = SkillPlanner(self.ai_client, self.skill_registry, self.support)

    def _default_conversation_key(self, user_token: Optional[str]) -> str:
        return build_conversation_key(user_token)

    def _get_history(self, conversation_key: str) -> list[dict[str, str]]:
        return self.memory_store.get_history(conversation_key)

    def _append_history(self, conversation_key: str, question: str, answer: str) -> None:
        self.memory_store.append_turn(conversation_key, question, answer)

    def _execute_skill_calls(
        self,
        skill_calls: list[tuple[str, dict]],
        request_context: RequestContext,
    ) -> list[str]:
        runtime = SkillRuntime(
            request_context=request_context,
            backend=self.backend,
            support=self.support,
        )
        observations: list[str] = []
        for skill_name, params in skill_calls:
            skill = self.skill_registry.get(skill_name)
            if skill is None:
                continue
            try:
                result = skill.run(params or {}, runtime)
                if result:
                    observations.append(result)
            except Exception as exc:
                print(f"Skill execution failed: {skill_name}: {exc}")
                observations.append("相关系统查询失败，请稍后重试。")
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
            cbs_answer = self.backend.chat_cbs(
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
        user_token: Optional[str] = None,
        conversation_key: Optional[str] = None,
        stream_mode: str = "default",
    ) -> str:
        question = (question or "").strip()
        if not question:
            return "问题不能为空。"

        conversation_key = conversation_key or self._default_conversation_key(user_token)
        request_context = RequestContext(
            user_token=user_token,
            conversation_key=conversation_key,
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
            return answer

        skill_calls, skip_primary_ai = self.planner.plan(question, request_context)
        observations = self._execute_skill_calls(skill_calls, request_context)
        data_summary = "\n\n".join(observations)
        final_prompt = build_final_answer_prompt(question, data_summary)
        history = self._get_history(conversation_key)

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
        return answer

    def chat(
        self,
        question: str,
        on_chunk: Optional[Callable[[str], None]] = None,
        user_token: Optional[str] = None,
        conversation_key: Optional[str] = None,
        stream_mode: str = "default",
    ) -> str:
        return self.process_question(
            question=question,
            on_chunk=on_chunk,
            user_token=user_token,
            conversation_key=conversation_key,
            stream_mode=stream_mode,
        )
