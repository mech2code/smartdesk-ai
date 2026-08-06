"""Ticket-status flow: validate email, then fetch live details from Jira."""
from __future__ import annotations

import logging
import re

from langchain_core.messages import AIMessage

from config import ConfigurationError
from memory.session import update_activity
from tools.get_ticket_status import get_ticket_status
from tools.jira_client import JiraAPIError

logger = logging.getLogger(__name__)
EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+(?:\.[\w-]+)+$")


def _lookup(email: str) -> str:
    try:
        return get_ticket_status.invoke({"email": email})
    except (ConfigurationError, JiraAPIError) as exc:
        logger.warning("Jira status lookup failed: %s", exc)
        return f"I couldn't reach Jira to check your tickets: {exc}"
    except Exception:
        logger.exception("Unexpected Jira status error")
        return "I couldn't check Jira because of an unexpected service error. Please try again later."


def run_status_flow(state: dict) -> dict:
    session = update_activity(dict(state.get("session") or {}))
    user_msg = state["messages"][-1].content.strip()
    email = session.get("email")

    if email:
        reply = _lookup(email)
        session["current_state"] = "GREETING"
    elif EMAIL_RE.fullmatch(user_msg):
        session["email"] = user_msg.lower()
        session["_ltm_loaded"] = False
        reply = _lookup(session["email"])
        session["current_state"] = "GREETING"
    else:
        if session.get("current_state") == "STATUS_COLLECTING_EMAIL":
            reply = "That email address is not valid. Please enter your **work email address**."
        else:
            reply = "To look up your Jira tickets, I'll need your **work email address**."
        session["current_state"] = "STATUS_COLLECTING_EMAIL"

    return {
        "messages": [AIMessage(content=reply)],
        "session": session,
        "intent": state.get("intent", "ticket_status"),
    }

