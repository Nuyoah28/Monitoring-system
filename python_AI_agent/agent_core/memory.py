from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field
from threading import RLock
from typing import Any


@dataclass
class ConversationMemory:
    history: list[dict[str, str]] = field(default_factory=list)
    state: dict[str, Any] = field(default_factory=dict)
    updated_at: float = field(default_factory=time.time)


class ConversationMemoryStore:
    def __init__(self, history_limit: int, ttl_seconds: int):
        self._history_limit = max(2, history_limit)
        self._ttl_seconds = max(60, ttl_seconds)
        self._lock = RLock()
        self._memories: dict[str, ConversationMemory] = {}

    def _cleanup_expired(self) -> None:
        now = time.time()
        expired_keys = [
            key for key, memory in self._memories.items()
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

    def get_history(self, conversation_key: str) -> list[dict[str, str]]:
        with self._lock:
            memory = self._memories.get(conversation_key)
            if memory is None:
                return []
            memory.updated_at = time.time()
            return copy.deepcopy(memory.history)

    def append_turn(self, conversation_key: str, question: str, answer: str) -> None:
        with self._lock:
            memory = self._get_or_create(conversation_key)
            memory.history.append({"role": "user", "content": question})
            memory.history.append({"role": "assistant", "content": answer})
            if len(memory.history) > self._history_limit:
                memory.history = memory.history[-self._history_limit:]

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
