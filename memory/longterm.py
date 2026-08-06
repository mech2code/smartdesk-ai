"""SQLite-backed long-term memory: read on session start, write on session end."""
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).parent.parent / "longterm.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS employees (
            email TEXT PRIMARY KEY,
            department TEXT,
            ticket_history TEXT,
            last_interaction TEXT
        )"""
    )
    conn.commit()
    return conn


def load_employee(email: str) -> dict:
    """Return stored employee data to hydrate a new session, or empty dict."""
    if not email:
        return {}
    conn = _get_conn()
    row = conn.execute(
        "SELECT department, ticket_history, last_interaction FROM employees WHERE email = ?",
        (email.lower(),),
    ).fetchone()
    conn.close()
    if not row:
        return {}
    department, ticket_history_raw, last_interaction = row
    try:
        ticket_history = json.loads(ticket_history_raw) if ticket_history_raw else []
    except json.JSONDecodeError:
        # Backward compatibility with the original comma-separated format.
        ticket_history = ticket_history_raw.split(",") if ticket_history_raw else []
    return {
        "department": department,
        "ticket_history": ticket_history,
        "last_interaction": last_interaction,
    }


def save_employee(email: str, session: dict):
    """Persist session data for the employee at session end."""
    if not email:
        return
    conn = _get_conn()
    ticket_history = json.dumps(session.get("ticket_history", []))
    conn.execute(
        """INSERT INTO employees (email, department, ticket_history, last_interaction)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(email) DO UPDATE SET
               department = excluded.department,
               ticket_history = excluded.ticket_history,
               last_interaction = excluded.last_interaction""",
        (
            email.lower(),
            session.get("department", ""),
            ticket_history,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def merge_employee_memory(session: dict, stored: dict) -> dict:
    """Merge durable employee data without overwriting the active flow."""
    merged = dict(session)
    if stored.get("department") and not merged.get("department"):
        merged["department"] = stored["department"]
    histories = [stored.get("ticket_history", []), merged.get("ticket_history", [])]
    merged["ticket_history"] = list(dict.fromkeys(item for group in histories for item in group))
    merged["_ltm_loaded"] = True
    return merged
