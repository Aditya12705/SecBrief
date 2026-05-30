"""SQLite audit log — sessions, plans, and enforcement decisions."""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent / "data" / "secbrief.db"

_schema_ready = False


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    """Create tables once. Safe to call multiple times."""
    global _schema_ready
    if _schema_ready:
        return

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_email TEXT NOT NULL,
                created_at TEXT NOT NULL,
                input_mode TEXT,
                summary TEXT
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                api_key TEXT NOT NULL UNIQUE,
                plan TEXT DEFAULT 'free',
                created_at TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            );
            CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_email ON sessions(user_email);
            CREATE INDEX IF NOT EXISTS idx_api_keys_email ON api_keys(email);
            CREATE INDEX IF NOT EXISTS idx_api_keys_key ON api_keys(api_key);
            """
        )
        conn.commit()
        _schema_ready = True
    finally:
        conn.close()


@contextmanager
def _connect():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def create_session(user_email: str, input_mode: str = "", summary: str = "") -> str:
    sid = str(uuid.uuid4())
    with _connect() as conn:
        conn.execute(
            "INSERT INTO sessions (id, user_email, created_at, input_mode, summary) VALUES (?, ?, ?, ?, ?)",
            (sid, user_email.strip().lower(), _utc_now(), input_mode, summary[:500]),
        )
    return sid


def log_event(session_id: str, event_type: str, payload: dict[str, Any]) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO events (session_id, event_type, payload, created_at) VALUES (?, ?, ?, ?)",
            (session_id, event_type, json.dumps(payload), _utc_now()),
        )


def get_session(session_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if not row:
            return None
        events = conn.execute(
            "SELECT event_type, payload, created_at FROM events WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
    return {
        "id": row["id"],
        "user_email": row["user_email"],
        "created_at": row["created_at"],
        "input_mode": row["input_mode"],
        "summary": row["summary"],
        "events": [
            {
                "event_type": e["event_type"],
                "payload": json.loads(e["payload"]),
                "created_at": e["created_at"],
            }
            for e in events
        ],
    }


def list_sessions(user_email: str, limit: int = 20) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, user_email, created_at, input_mode, summary FROM sessions "
            "WHERE user_email = ? ORDER BY created_at DESC LIMIT ?",
            (user_email.strip().lower(), limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_api_key_by_email(email: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM api_keys WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()
    return dict(row) if row else None


def get_api_key_by_key(api_key: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM api_keys WHERE api_key = ?",
            (api_key,),
        ).fetchone()
    return dict(row) if row else None


def create_api_key(email: str, api_key: str, plan: str = "free") -> dict[str, Any]:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO api_keys (email, api_key, plan, created_at, is_active) VALUES (?, ?, ?, ?, ?)",
            (email.strip().lower(), api_key, plan, _utc_now(), 1),
        )
        row = conn.execute(
            "SELECT * FROM api_keys WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()
    return dict(row)
