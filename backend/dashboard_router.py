"""
dashboard_router.py — NEW FILE — Pulse dashboard backend.
Read-only queries on the existing SecBrief SQLite database.
Mount by adding these two lines to the BOTTOM of main.py:
    from dashboard_router import router as dashboard_router
    app.include_router(dashboard_router)
"""

from __future__ import annotations

import json
import os
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

# Matches db.py: DB_PATH = Path(__file__).resolve().parent / "data" / "secbrief.db"
_DB_PATH = Path(__file__).resolve().parent / "data" / "secbrief.db"


def _connect_ro() -> sqlite3.Connection:
    """Open the existing DB in read-only mode (uri mode). Never writes."""
    uri = f"file:{_DB_PATH}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _safe_connect():
    """Return a connection or None if the DB file doesn't exist yet."""
    if not _DB_PATH.exists():
        return None
    try:
        return _connect_ro()
    except Exception:
        return None


def _today_prefix() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


@router.get("/api/dashboard")
def get_dashboard() -> dict:
    """
    Aggregated stats for the Pulse dashboard.

    Schema used (from db.py):
      sessions(id, user_email, created_at, input_mode, summary)
      events(id, session_id, event_type, payload JSON, created_at)

    payload for 'plan_verify' events contains:
      { decisions: [{action, mcp, status, ...}], armoriq_live, receipt, ... }
    payload for 'explain' / 'audit_code' events contains:
      { severity, source }
    payload for 'scan' events contains:
      { repo, deep }

    All fields are safe-defaulted — never crashes if DB is empty or missing.
    """
    _empty = {
        "total_scans": 0,
        "avg_risk_score": 0.0,
        "steps_blocked": 0,
        "active_users": 0,
        "owasp_breakdown": [],
        "enforcement_summary": {"allowed": 0, "blocked": 0, "held": 0},
        "recent_sessions": [],
    }

    conn = _safe_connect()
    if conn is None:
        return _empty

    try:
        with conn:
            # ── 1. total scans ──────────────────────────────────────────────
            total_scans = 0
            try:
                row = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()
                total_scans = int(row[0]) if row else 0
            except Exception:
                pass

            # ── 2. avg risk score — stored in plan_verify receipt.total_steps
            #    The analysis doesn't store risk_score in events directly.
            #    We parse severity counts and map them → approximate score.
            #    high→8, medium→5, low→2, critical→9, info→1
            severity_map = {
                "critical": 9.0, "high": 8.0, "medium": 5.0,
                "low": 2.0, "info": 1.0, "informational": 1.0,
            }
            avg_risk_score = 0.0
            try:
                evt_rows = conn.execute(
                    "SELECT payload FROM events WHERE event_type IN ('explain','audit_code','scan')"
                ).fetchall()
                scores = []
                for r in evt_rows:
                    try:
                        p = json.loads(r["payload"])
                        sev = str(p.get("severity", "")).lower()
                        if sev in severity_map:
                            scores.append(severity_map[sev])
                    except Exception:
                        pass
                if scores:
                    avg_risk_score = round(sum(scores) / len(scores), 2)
            except Exception:
                pass

            # ── 3. steps blocked ────────────────────────────────────────────
            steps_blocked = 0
            try:
                plan_rows = conn.execute(
                    "SELECT payload FROM events WHERE event_type = 'plan_verify'"
                ).fetchall()
                for r in plan_rows:
                    try:
                        p = json.loads(r["payload"])
                        decisions = p.get("decisions", [])
                        steps_blocked += sum(
                            1 for d in decisions
                            if isinstance(d, dict) and d.get("status") == "block"
                        )
                    except Exception:
                        pass
            except Exception:
                pass

            # ── 4. active users today (unique emails) ───────────────────────
            active_users = 0
            try:
                today = _today_prefix()
                row = conn.execute(
                    "SELECT COUNT(DISTINCT user_email) FROM sessions WHERE created_at LIKE ?",
                    (f"{today}%",),
                ).fetchone()
                active_users = int(row[0]) if row else 0
            except Exception:
                pass

            # ── 5. OWASP breakdown — parse from event payloads ──────────────
            owasp_counter: Counter = Counter()
            try:
                all_payloads = conn.execute(
                    "SELECT payload FROM events"
                ).fetchall()
                for r in all_payloads:
                    try:
                        p = json.loads(r["payload"])
                        # Stored as "owasp_category" in analysis payloads
                        cat = p.get("owasp_category", "")
                        if cat:
                            # Normalise to short form e.g. "A03 · Injection"
                            owasp_counter[str(cat)] += 1
                        # Also check nested analysis dict
                        analysis = p.get("analysis", {})
                        if isinstance(analysis, dict):
                            cat2 = analysis.get("owasp_category", "")
                            if cat2:
                                owasp_counter[str(cat2)] += 1
                    except Exception:
                        pass
            except Exception:
                pass

            owasp_breakdown = [
                {"category": cat, "count": cnt}
                for cat, cnt in owasp_counter.most_common(5)
            ]

            # ── 6. enforcement summary ──────────────────────────────────────
            enforcement = {"allowed": 0, "blocked": 0, "held": 0}
            try:
                for r in plan_rows:
                    try:
                        p = json.loads(r["payload"])
                        for d in p.get("decisions", []):
                            if not isinstance(d, dict):
                                continue
                            s = d.get("status", "")
                            if s == "allow":
                                enforcement["allowed"] += 1
                            elif s == "block":
                                enforcement["blocked"] += 1
                            elif s == "hold":
                                enforcement["held"] += 1
                    except Exception:
                        pass
            except Exception:
                pass

            # ── 7. recent sessions (last 10) ────────────────────────────────
            recent_sessions: list[dict] = []
            try:
                sess_rows = conn.execute(
                    """
                    SELECT id, user_email, created_at, input_mode, summary
                    FROM sessions
                    ORDER BY created_at DESC
                    LIMIT 10
                    """
                ).fetchall()

                for sess in sess_rows:
                    sid = sess["id"]
                    # Pull all events for this session
                    evts = conn.execute(
                        "SELECT event_type, payload FROM events WHERE session_id = ?",
                        (sid,),
                    ).fetchall()

                    owasp_tags: list[str] = []
                    session_risk: float = 0.0
                    blocked_count = 0
                    source_str = sess["input_mode"] or "unknown"

                    for evt in evts:
                        try:
                            p = json.loads(evt["payload"])
                            etype = evt["event_type"]

                            if etype in ("explain", "audit_code", "scan"):
                                sev = str(p.get("severity", "")).lower()
                                if sev in severity_map:
                                    session_risk = max(session_risk, severity_map[sev])
                                repo = p.get("repo", "")
                                if repo:
                                    source_str = repo

                                cat = p.get("owasp_category", "")
                                if cat and cat not in owasp_tags:
                                    owasp_tags.append(cat)

                            elif etype == "plan_verify":
                                for d in p.get("decisions", []):
                                    if isinstance(d, dict) and d.get("status") == "block":
                                        blocked_count += 1

                        except Exception:
                            pass

                    # Derive short OWASP codes
                    short_tags = []
                    for t in owasp_tags:
                        # Extract "A03" prefix if present, else use first word
                        parts = t.split()
                        short_tags.append(parts[0] if parts else t)

                    recent_sessions.append(
                        {
                            "email": sess["user_email"],
                            "source": source_str,
                            "risk_score": round(session_risk, 1),
                            "owasp_tags": short_tags,
                            "blocked_count": blocked_count,
                            "timestamp": sess["created_at"],
                        }
                    )
            except Exception:
                pass

        return {
            "total_scans": total_scans,
            "avg_risk_score": avg_risk_score,
            "steps_blocked": steps_blocked,
            "active_users": active_users,
            "owasp_breakdown": owasp_breakdown,
            "enforcement_summary": enforcement,
            "recent_sessions": recent_sessions,
        }

    except Exception:
        return _empty
    finally:
        conn.close()
