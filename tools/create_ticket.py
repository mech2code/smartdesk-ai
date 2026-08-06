"""Create a Jira support ticket and persist its employee mapping locally."""
from __future__ import annotations

from langchain_core.tools import tool

from tools.jira_client import JiraClient
from tools.ticket_store import save_ticket_mapping


def _get_jira_client() -> JiraClient:
    return JiraClient()


@tool
def create_ticket(
    email: str,
    summary: str,
    description: str,
    category: str,
    priority: str,
) -> str:
    """Create a Jira support ticket after the employee confirms the full draft."""
    issue = _get_jira_client().create_issue(
        summary=summary,
        description=description,
        category=category,
        priority=priority,
    )
    save_ticket_mapping(
        email=email,
        jira_key=issue["key"],
        summary=summary,
        category=category,
        priority=priority,
        issue_url=issue["url"],
    )
    return (
        "Ticket created successfully!\n"
        f"- **Ticket ID**: [{issue['key']}]({issue['url']})\n"
        f"- **Summary**: {summary}\n"
        f"- **Priority**: {priority.title()}\n"
        "- **Status**: Open\n\n"
        f"Updates will be associated with **{email.lower()}**."
    )

