"""Short-lived conversation state helpers."""
from __future__ import annotations

from datetime import datetime, timezone

from config import get_app_settings


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_session(*, email: str | None = None) -> dict:
    return {
        "email": email,
        "current_state": "GREETING",
        "summary": None,
        "description": None,
        "category": None,
        "priority": None,
        "editing_field": None,
        "department": None,
        "ticket_history": [],
        "last_activity": _now_iso(),
        "_ltm_loaded": False,
    }


def update_activity(session: dict) -> dict:
    updated = dict(session)
    updated["last_activity"] = _now_iso()
    return updated


def session_is_expired(session: dict) -> bool:
    raw = session.get("last_activity")
    if not raw:
        return False
    try:
        last_activity = datetime.fromisoformat(raw)
        if last_activity.tzinfo is None:
            last_activity = last_activity.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return True
    elapsed = datetime.now(timezone.utc) - last_activity.astimezone(timezone.utc)
    return elapsed.total_seconds() > get_app_settings().session_timeout_minutes * 60

