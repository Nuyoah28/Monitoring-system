from __future__ import annotations

# AI辅助生成：本文件中的会话事实记忆存储与清理逻辑由 GPT-5 Codex 协助完成，2026-04-04。

import copy
import json
import math
import re
import sqlite3
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any


@dataclass
class VectorTurn:
    question: str
    answer: str
    embedding: dict[str, float]
    sequence: int
    updated_at: float


class ConversationMemoryStore:
    def __init__(self, history_limit: int, ttl_seconds: int, db_path: str):
        self._turn_limit = max(2, history_limit)
        self._ttl_seconds = max(60, ttl_seconds)
        self._db_path = str(db_path)
        self._lock = RLock()
        self._conn = self._init_db(self._db_path)

    def _init_db(self, db_path: str) -> sqlite3.Connection:
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_file, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_key TEXT PRIMARY KEY,
                updated_at REAL NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS vector_turns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_key TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                embedding_json TEXT NOT NULL,
                updated_at REAL NOT NULL,
                UNIQUE(conversation_key, sequence)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_state (
                conversation_key TEXT NOT NULL,
                state_key TEXT NOT NULL,
                state_value_json TEXT NOT NULL,
                updated_at REAL NOT NULL,
                PRIMARY KEY (conversation_key, state_key)
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_turns_conv_seq ON vector_turns(conversation_key, sequence)")
        conn.commit()
        return conn

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

    def _touch_conversation(self, conversation_key: str, now_ts: float) -> None:
        self._conn.execute(
            """
            INSERT INTO conversations(conversation_key, updated_at)
            VALUES(?, ?)
            ON CONFLICT(conversation_key) DO UPDATE SET updated_at=excluded.updated_at
            """,
            (conversation_key, now_ts),
        )

    def _cleanup_expired(self) -> None:
        now = time.time()
        expire_before = now - self._ttl_seconds
        expired_keys = [
            row[0]
            for row in self._conn.execute(
                "SELECT conversation_key FROM conversations WHERE updated_at < ?",
                (expire_before,),
            ).fetchall()
        ]
        if not expired_keys:
            return

        for conversation_key in expired_keys:
            self._conn.execute("DELETE FROM vector_turns WHERE conversation_key=?", (conversation_key,))
            self._conn.execute("DELETE FROM conversation_state WHERE conversation_key=?", (conversation_key,))
            self._conn.execute("DELETE FROM conversations WHERE conversation_key=?", (conversation_key,))
        self._conn.commit()

    def _load_turns(self, conversation_key: str) -> list[VectorTurn]:
        rows = self._conn.execute(
            """
            SELECT sequence, question, answer, embedding_json, updated_at
            FROM vector_turns
            WHERE conversation_key=?
            ORDER BY sequence ASC
            """,
            (conversation_key,),
        ).fetchall()
        turns: list[VectorTurn] = []
        for sequence, question, answer, embedding_json, updated_at in rows:
            try:
                embedding = json.loads(embedding_json)
                if not isinstance(embedding, dict):
                    embedding = {}
            except Exception:
                embedding = {}
            turns.append(
                VectorTurn(
                    question=question,
                    answer=answer,
                    embedding=embedding,
                    sequence=int(sequence),
                    updated_at=float(updated_at),
                )
            )
        return turns

    def get_history(
        self,
        conversation_key: str,
        *,
        query: str = "",
        top_k: int = 4,
    ) -> list[dict[str, str]]:
        with self._lock:
            self._cleanup_expired()
            turns = self._load_turns(conversation_key)
            if not turns:
                return []

            self._touch_conversation(conversation_key, time.time())

            selected: list[VectorTurn]
            if query.strip():
                query_embedding = self._embed_text(query)
                ranked = sorted(
                    turns,
                    key=lambda turn: self._cosine_similarity(query_embedding, turn.embedding),
                    reverse=True,
                )
                selected = ranked[: max(1, top_k)]
            else:
                selected = turns[-max(1, top_k) :]

            selected = sorted(selected, key=lambda item: item.sequence)
            history: list[dict[str, str]] = []
            for turn in selected:
                history.append({"role": "user", "content": turn.question})
                history.append({"role": "assistant", "content": turn.answer})
            return copy.deepcopy(history)

    def append_turn(self, conversation_key: str, question: str, answer: str) -> None:
        with self._lock:
            self._cleanup_expired()
            now_ts = time.time()
            self._touch_conversation(conversation_key, now_ts)

            row = self._conn.execute(
                "SELECT COALESCE(MAX(sequence), 0) FROM vector_turns WHERE conversation_key=?",
                (conversation_key,),
            ).fetchone()
            sequence = (int(row[0]) if row and row[0] is not None else 0) + 1

            turn = VectorTurn(
                question=question,
                answer=answer,
                embedding=self._embed_text(f"{question}\n{answer}"),
                sequence=sequence,
                updated_at=now_ts,
            )
            self._conn.execute(
                """
                INSERT INTO vector_turns(
                    conversation_key, sequence, question, answer, embedding_json, updated_at
                ) VALUES(?, ?, ?, ?, ?, ?)
                """,
                (
                    conversation_key,
                    turn.sequence,
                    turn.question,
                    turn.answer,
                    json.dumps(turn.embedding, ensure_ascii=False),
                    turn.updated_at,
                ),
            )

            count_row = self._conn.execute(
                "SELECT COUNT(1) FROM vector_turns WHERE conversation_key=?",
                (conversation_key,),
            ).fetchone()
            count = int(count_row[0]) if count_row and count_row[0] is not None else 0
            overflow = max(0, count - self._turn_limit)
            if overflow > 0:
                self._conn.execute(
                    """
                    DELETE FROM vector_turns
                    WHERE id IN (
                        SELECT id FROM vector_turns
                        WHERE conversation_key=?
                        ORDER BY sequence ASC
                        LIMIT ?
                    )
                    """,
                    (conversation_key, overflow),
                )
            self._conn.commit()

    def get_state(self, conversation_key: str) -> dict[str, Any]:
        with self._lock:
            self._cleanup_expired()
            rows = self._conn.execute(
                "SELECT state_key, state_value_json FROM conversation_state WHERE conversation_key=?",
                (conversation_key,),
            ).fetchall()
            if not rows:
                return {}

            self._touch_conversation(conversation_key, time.time())
            state: dict[str, Any] = {}
            for state_key, value_json in rows:
                try:
                    state[state_key] = json.loads(value_json)
                except Exception:
                    continue
            return copy.deepcopy(state)

    def update_state(self, conversation_key: str, **updates: Any) -> None:
        with self._lock:
            self._cleanup_expired()
            now_ts = time.time()
            self._touch_conversation(conversation_key, now_ts)
            for key, value in updates.items():
                if value is not None:
                    self._conn.execute(
                        """
                        INSERT INTO conversation_state(conversation_key, state_key, state_value_json, updated_at)
                        VALUES(?, ?, ?, ?)
                        ON CONFLICT(conversation_key, state_key)
                        DO UPDATE SET state_value_json=excluded.state_value_json, updated_at=excluded.updated_at
                        """,
                        (conversation_key, key, json.dumps(copy.deepcopy(value), ensure_ascii=False), now_ts),
                    )
            self._conn.commit()
