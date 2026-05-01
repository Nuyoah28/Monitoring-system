import os
import sqlite3
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from config import DevConfig as Config
from util.Logger import setup_logger

logger = setup_logger()

_db_lock = threading.Lock()
_sync_thread = None
_stop_event = threading.Event()
_sync_callback = None


def _algorithm_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cache_root() -> str:
    configured_dir = getattr(Config, "ALARM_CACHE_DIR", "runtime/alarm_cache")
    if os.path.isabs(configured_dir):
        return configured_dir
    return os.path.join(_algorithm_root(), configured_dir)


def _db_path() -> str:
    return os.path.join(_cache_root(), getattr(Config, "ALARM_CACHE_DB", "alarm_cache.sqlite3"))


def _clip_root() -> str:
    return os.path.join(_cache_root(), getattr(Config, "ALARM_CACHE_CLIP_DIR", "clips"))


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path(), timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def init_cache() -> None:
    os.makedirs(_clip_root(), exist_ok=True)
    with _db_lock:
        with _connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pending_alarm_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    clip_id TEXT NOT NULL,
                    camera_id INTEGER NOT NULL,
                    case_type INTEGER NOT NULL,
                    clip_path TEXT,
                    occurred_at TEXT NOT NULL,
                    sync_status TEXT NOT NULL DEFAULT 'pending',
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(clip_id, camera_id, case_type)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_alarm_cache_status ON pending_alarm_cache(sync_status, updated_at)"
            )
            conn.commit()


def save_clip_frames(frames: List[Any], clip_id: str) -> Optional[str]:
    if not frames:
        return None

    from util import UploadCos

    init_cache()
    clip_path = os.path.join(_clip_root(), f"{clip_id}.flv")
    UploadCos.saveFrames2Flv(frames, clip_path)

    return clip_path if os.path.exists(clip_path) else None


def enqueue_alarm(clip_id: str, camera_id: int, case_type: int, clip_path: Optional[str], occurred_at: str) -> None:
    init_cache()
    now = _now_text()
    with _db_lock:
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO pending_alarm_cache
                    (clip_id, camera_id, case_type, clip_path, occurred_at, sync_status, retry_count, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'pending', 0, ?, ?)
                ON CONFLICT(clip_id, camera_id, case_type) DO UPDATE SET
                    clip_path = COALESCE(excluded.clip_path, pending_alarm_cache.clip_path),
                    sync_status = CASE
                        WHEN pending_alarm_cache.sync_status = 'synced' THEN 'synced'
                        ELSE 'pending'
                    END,
                    updated_at = excluded.updated_at
                """,
                (clip_id, camera_id, case_type, clip_path, occurred_at, now, now),
            )
            conn.commit()


def update_clip_path(clip_id: str, clip_path: str) -> None:
    now = _now_text()
    with _db_lock:
        with _connect() as conn:
            conn.execute(
                """
                UPDATE pending_alarm_cache
                SET clip_path = ?, updated_at = ?
                WHERE clip_id = ?
                """,
                (clip_path, now, clip_id),
            )
            conn.commit()


def mark_synced(clip_id: str, camera_id: int, case_type: int) -> None:
    now = _now_text()
    with _db_lock:
        with _connect() as conn:
            conn.execute(
                """
                UPDATE pending_alarm_cache
                SET sync_status = 'synced', last_error = NULL, updated_at = ?
                WHERE clip_id = ? AND camera_id = ? AND case_type = ?
                """,
                (now, clip_id, camera_id, case_type),
            )
            conn.commit()


def mark_failed(clip_id: str, camera_id: int, case_type: int, error: Exception) -> None:
    now = _now_text()
    with _db_lock:
        with _connect() as conn:
            conn.execute(
                """
                UPDATE pending_alarm_cache
                SET sync_status = 'pending',
                    retry_count = retry_count + 1,
                    last_error = ?,
                    updated_at = ?
                WHERE clip_id = ? AND camera_id = ? AND case_type = ?
                """,
                (str(error)[:500], now, clip_id, camera_id, case_type),
            )
            conn.commit()


def mark_clip_failed(clip_id: str, error: Exception) -> None:
    now = _now_text()
    with _db_lock:
        with _connect() as conn:
            conn.execute(
                """
                UPDATE pending_alarm_cache
                SET sync_status = 'pending',
                    retry_count = retry_count + 1,
                    last_error = ?,
                    updated_at = ?
                WHERE clip_id = ?
                """,
                (str(error)[:500], now, clip_id),
            )
            conn.commit()


def get_pending_alarms(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    init_cache()
    batch_size = limit or getattr(Config, "ALARM_SYNC_BATCH_SIZE", 20)
    with _db_lock:
        with _connect() as conn:
            rows = conn.execute(
                """
                SELECT id, clip_id, camera_id, case_type, clip_path, occurred_at, retry_count, last_error
                FROM pending_alarm_cache
                WHERE sync_status = 'pending'
                ORDER BY id ASC
                LIMIT ?
                """,
                (batch_size,),
            ).fetchall()
    return [dict(row) for row in rows]


def sync_pending_once() -> int:
    if _sync_callback is None:
        return 0

    synced_count = 0
    for item in get_pending_alarms():
        try:
            _sync_callback(item)
            mark_synced(item["clip_id"], item["camera_id"], item["case_type"])
            synced_count += 1
        except Exception as exc:
            mark_failed(item["clip_id"], item["camera_id"], item["case_type"], exc)
            logger.warning("pending alarm sync failed: %s", exc)
    return synced_count


def start_sync_worker(sync_callback) -> None:
    global _sync_callback, _sync_thread
    if not getattr(Config, "ALARM_CACHE_ENABLED", True):
        return
    init_cache()
    _sync_callback = sync_callback
    if _sync_thread and _sync_thread.is_alive():
        return

    def _worker() -> None:
        while not _stop_event.is_set():
            try:
                synced = sync_pending_once()
                if synced:
                    logger.info("synced %s cached alarms", synced)
            except Exception as exc:
                logger.warning("alarm cache sync worker failed: %s", exc)
            _stop_event.wait(getattr(Config, "ALARM_SYNC_INTERVAL_SECONDS", 10))

    _stop_event.clear()
    _sync_thread = threading.Thread(target=_worker, name="alarm-cache-sync", daemon=True)
    _sync_thread.start()


def stop_sync_worker() -> None:
    _stop_event.set()
