from __future__ import annotations

import copy
import math
import re
import time
from collections import Counter
from dataclasses import dataclass, field
from threading import RLock
from typing import Any


@dataclass
class VectorTurn:
    question: str
    answer: str
    embedding: dict[str, float]
    sequence: int
    updated_at: float = field(default_factory=time.time)


@dataclass
class ConversationMemory:
    turns: list[VectorTurn] = field(default_factory=list)
    state: dict[str, Any] = field(default_factory=dict)
    updated_at: float = field(default_factory=time.time)


class ConversationMemoryStore:
    def __init__(self, history_limit: int, ttl_seconds: int):
        self._turn_limit = max(2, history_limit)
        self._ttl_seconds = max(60, ttl_seconds)
        self._lock = RLock()
        self._memories: dict[str, ConversationMemory] = {}

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"[a-zA-Z0-9_]+|[\u4e00-\u9fff]", (text or "").lower())

    @classmethod
    def _embed_text(cls, text: str) -> dict[str, float]:
        tokens = cls._tokenize(text)
        if not tokens:
            return {}
        counts = Counter(tokens)
        norm = math.sqrt(sum(value * value for value in counts.values()))
        if norm <= 0:
            return {}
        return {key: value / norm for key, value in counts.items()}

    @staticmethod
    def _cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
        if not left or not right:
            return 0.0
        if len(left) > len(right):
            left, right = right, left
        return sum(value * right.get(key, 0.0) for key, value in left.items())

    def _cleanup_expired(self) -> None:
        now = time.time()
        expired_keys = [
            key
            for key, memory in self._memories.items()
            if now - memory.updated_at > self._ttl_seconds
        ]
        for key in expired_keys:
            self._memories.pop(key, None)

    def _get_or_create(self, conversation_key: str) -> ConversationMemory:
        self._cleanup_expired()
        memory = self._memories.get(conversation_key)
        if memory is None:
            memory = ConversationMemory()
            self._memories[conversation_key] = memory
        memory.updated_at = time.time()
        return memory

    def get_history(
        self,
        conversation_key: str,
        *,
        query: str = "",
        top_k: int = 4,
    ) -> list[dict[str, str]]:
        with self._lock:
            memory = self._memories.get(conversation_key)
            if memory is None:
                return []
            memory.updated_at = time.time()

            if not memory.turns:
                return []

            selected: list[VectorTurn]
            if query.strip():
                query_embedding = self._embed_text(query)
                ranked = sorted(
                    memory.turns,
                    key=lambda turn: self._cosine_similarity(query_embedding, turn.embedding),
                    reverse=True,
                )
                selected = ranked[: max(1, top_k)]
            else:
                selected = memory.turns[-max(1, top_k) :]

            selected = sorted(selected, key=lambda item: item.sequence)
            history: list[dict[str, str]] = []
            for turn in selected:
                history.append({"role": "user", "content": turn.question})
                history.append({"role": "assistant", "content": turn.answer})
            return copy.deepcopy(history)

    def append_turn(self, conversation_key: str, question: str, answer: str) -> None:
        with self._lock:
            memory = self._get_or_create(conversation_key)
            turn = VectorTurn(
                question=question,
                answer=answer,
                embedding=self._embed_text(f"{question}\n{answer}"),
                sequence=(memory.turns[-1].sequence + 1) if memory.turns else 1,
            )
            memory.turns.append(turn)
            if len(memory.turns) > self._turn_limit:
                memory.turns = memory.turns[-self._turn_limit :]

    def get_state(self, conversation_key: str) -> dict[str, Any]:
        with self._lock:
            memory = self._memories.get(conversation_key)
            if memory is None:
                return {}
            memory.updated_at = time.time()
            return copy.deepcopy(memory.state)

    def update_state(self, conversation_key: str, **updates: Any) -> None:
        with self._lock:
            memory = self._get_or_create(conversation_key)
            for key, value in updates.items():
                if value is not None:
                    memory.state[key] = copy.deepcopy(value)
