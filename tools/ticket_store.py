"""SQLite persistence for employee-email to Jira-issue mappings."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "tickets.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS jira_ticket_mappings (
            jira_key TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            summary TEXT NOT NULL,
            category TEXT NOT NULL,
            priority TEXT NOT NULL,
            issue_url TEXT NOT NULL,
            created_at TEXT NOT NULL
        )"""
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_jira_ticket_email ON jira_ticket_mappings(email)"
    )
    conn.commit()
    return conn


def save_ticket_mapping(
    *,
    email: str,
    jira_key: str,
    summary: str,
    category: str,
    priority: str,
    issue_url: str,
) -> None:
    conn = _get_conn()
    try:
        with conn:
            conn.execute(
                """INSERT INTO jira_ticket_mappings
                   (jira_key, email, summary, category, priority, issue_url, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(jira_key) DO UPDATE SET
                       email = excluded.email,
                       summary = excluded.summary,
                       category = excluded.category,
                       priority = excluded.priority,
                       issue_url = excluded.issue_url""",
                (
                    jira_key,
                    email.lower(),
                    summary,
                    category,
                    priority,
                    issue_url,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
    finally:
        conn.close()


def get_ticket_mappings(email: str, limit: int = 10) -> list[dict]:
    conn = _get_conn()
    try:
        rows = conn.execute(
            """SELECT jira_key, summary, category, priority, issue_url, created_at
               FROM jira_ticket_mappings
               WHERE email = ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (email.lower(), limit),
        ).fetchall()
    finally:
        conn.close()
    return [dict(row) for row in rows]
