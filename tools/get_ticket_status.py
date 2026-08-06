"""Fetch live Jira status for tickets mapped to an employee email."""
from __future__ import annotations

from langchain_core.tools import tool

from tools.jira_client import JiraAPIError, JiraClient
from tools.ticket_store import get_ticket_mappings


def _get_jira_client() -> JiraClient:
    return JiraClient()


@tool
def get_ticket_status(email: str) -> str:
    """Fetch live Jira status for up to ten tickets belonging to an employee."""
    mappings = get_ticket_mappings(email)
    if not mappings:
        return (
            f"No tickets found for **{email.lower()}**. "
            "If this looks wrong, confirm that the ticket was created through SmartDesk AI."
        )

    client = _get_jira_client()
    lines = [f"Found **{len(mappings)}** ticket(s) for {email.lower()}:\n"]
    for mapping in mappings:
        key = mapping["jira_key"]
        try:
            issue = client.get_issue(key)
        except JiraAPIError as exc:
            lines.append(f"- **{key}** — Jira status is temporarily unavailable ({exc}).")
            continue
        lines.append(
            f"- **[{issue['key']}]({issue['url']})** [{issue['status']}] — {issue['summary']}\n"
            f"  Priority: {issue['priority']} | Assignee: {issue['assignee']}\n"
            f"  Latest comment: {issue['latest_comment']}"
        )
    return "\n".join(lines)

