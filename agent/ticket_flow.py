"""Ticket-creation state machine with explicit human confirmation."""
from __future__ import annotations

import logging
import re

from langchain_core.messages import AIMessage

from config import ConfigurationError
from memory.session import update_activity
from tools.create_ticket import create_ticket
from tools.jira_client import JiraAPIError

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+(?:\.[\w-]+)+$")
JIRA_KEY_RE = re.compile(r"\b[A-Z][A-Z0-9_]*-\d+\b")
YES_RESPONSES = {
    "yes",
    "yes please",
    "yes, please",
    "yes submit",
    "yes, submit",
    "confirm",
    "confirm and submit",
}
NO_RESPONSES = {"no", "cancel", "nevermind", "never mind", "stop"}
VALID_PRIORITIES = {"critical", "high", "medium", "low"}
VALID_CATEGORIES = {"it": "IT", "hr": "HR", "general": "General"}
MAX_SUMMARY_LENGTH = 255
MAX_DESCRIPTION_LENGTH = 5000

PRIORITY_KEYWORDS = {
    "critical": ["critical", "urgent", "asap", "emergency", "system down", "outage"],
    "high": ["high", "important", "soon", "blocking", "cannot work"],
    "low": ["low", "minor", "small", "whenever"],
}


def _infer_priority(text: str) -> str:
    text_lower = text.lower()
    for priority, keywords in PRIORITY_KEYWORDS.items():
        if any(keyword in text_lower for keyword in keywords):
            return priority
    return "medium"


def _infer_category(text: str) -> str:
    text_lower = text.lower()
    if any(kw in text_lower for kw in ("vpn", "password", "mfa", "software", "email", "wifi", "wi-fi", "laptop", "hardware", "monitor", "printer")):
        return "IT"
    if any(kw in text_lower for kw in ("leave", "payroll", "salary", "benefit", "hr", "policy", "remote", "performance")):
        return "HR"
    return "General"


def _clear_ticket_fields(session: dict) -> dict:
    session.update(
        {
            "summary": None,
            "description": None,
            "category": None,
            "priority": None,
            "editing_field": None,
        }
    )
    return session


def _draft(session: dict, intro: str = "Please review your ticket before I submit it:") -> str:
    return (
        f"{intro}\n\n"
        f"- **Email**: {session.get('email')}\n"
        f"- **Summary**: {session.get('summary')}\n"
        f"- **Description**: {session.get('description')}\n"
        f"- **Category**: {session.get('category', 'General')}\n"
        f"- **Priority**: {session.get('priority', 'medium').title()}\n\n"
        "Type **yes** to submit, **cancel** to stop, or tell me what to change."
    )


def _response(state: dict, session: dict, reply: str) -> dict:
    return {
        "messages": [AIMessage(content=reply)],
        "session": session,
        "intent": state.get("intent", "ticket_create"),
    }


def _inline_value(message: str, field: str) -> str | None:
    aliases = {
        "email": "email|email address",
        "summary": "summary|title",
        "description": "description|details?",
        "category": "category|team",
        "priority": "priority",
    }[field]
    match = re.search(
        rf"(?:change|update|set)\s+(?:the\s+)?(?:{aliases})\s+(?:to\s+|:\s*)(.+)$",
        message,
        flags=re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def _apply_change(session: dict, field: str, value: str) -> str | None:
    value = value.strip()
    if not value:
        return f"The {field} cannot be empty."
    if field == "email":
        if len(value) > 254 or not EMAIL_RE.fullmatch(value):
            return "That does not look like a valid work email address."
        session["email"] = value.lower()
        session["_ltm_loaded"] = False
    elif field == "priority":
        normalized = value.lower()
        if normalized not in VALID_PRIORITIES:
            return "Priority must be critical, high, medium, or low."
        session["priority"] = normalized
    elif field == "category":
        normalized = value.lower()
        if normalized not in VALID_CATEGORIES:
            return "Category must be IT, HR, or General."
        session["category"] = VALID_CATEGORIES[normalized]
    else:
        if field == "summary" and len(value) > MAX_SUMMARY_LENGTH:
            return f"The summary must be {MAX_SUMMARY_LENGTH} characters or fewer."
        if field == "description" and len(value) > MAX_DESCRIPTION_LENGTH:
            return f"The description must be {MAX_DESCRIPTION_LENGTH} characters or fewer."
        session[field] = value
        if field == "summary":
            session["category"] = _infer_category(value)
    return None


def _requested_field(message: str) -> str | None:
    lowered = message.lower()
    for field, aliases in {
        "email": ("email",),
        "summary": ("summary", "title"),
        "description": ("description", "detail"),
        "category": ("category", "team"),
        "priority": ("priority",),
    }.items():
        if any(alias in lowered for alias in aliases):
            return field
    return None


def run_ticket_flow(state: dict) -> dict:
    session = update_activity(dict(state.get("session") or {}))
    user_msg = state["messages"][-1].content.strip()
    current_state = session.get("current_state", "GREETING")

    if current_state == "ESCALATION_CONFIRMING":
        lowered = user_msg.lower()
        if lowered in YES_RESPONSES:
            if session.get("email"):
                session["current_state"] = "COLLECTING_DESCRIPTION"
                reply = "Please provide more detail about the issue and when it started."
            else:
                session["current_state"] = "COLLECTING_EMAIL"
                reply = "I can create that ticket. What is your **work email address**?"
        elif lowered in NO_RESPONSES:
            _clear_ticket_fields(session)
            session["current_state"] = "GREETING"
            reply = "No problem—I have not created a ticket. What else can I help with?"
        else:
            reply = "Would you like me to create a support ticket? Please answer **yes** or **no**."

    elif current_state in {"GREETING", "DONE"}:
        _clear_ticket_fields(session)
        if session.get("email"):
            session["current_state"] = "COLLECTING_SUMMARY"
            reply = "I'll help you create a Jira ticket. Briefly, **what is the issue?**"
        else:
            session["current_state"] = "COLLECTING_EMAIL"
            reply = "I'll help you create a Jira ticket. What is your **work email address**?"

    elif current_state == "COLLECTING_EMAIL":
        if len(user_msg) > 254 or not EMAIL_RE.fullmatch(user_msg):
            reply = "That doesn't look like a valid email address. Please enter your **work email**."
        else:
            session["email"] = user_msg.lower()
            session["_ltm_loaded"] = False
            if session.get("summary"):
                session["current_state"] = "COLLECTING_DESCRIPTION"
                reply = (
                    f"I've kept your issue summary as *\"{session['summary']}\"*. "
                    "Please provide more detail and when it started."
                )
            else:
                session["current_state"] = "COLLECTING_SUMMARY"
                reply = "Thanks. Briefly, **what is the issue?**"

    elif current_state == "COLLECTING_SUMMARY":
        if not user_msg:
            reply = "Please provide a short summary of the issue."
        elif len(user_msg) > MAX_SUMMARY_LENGTH:
            reply = f"Please keep the summary to {MAX_SUMMARY_LENGTH} characters or fewer."
        else:
            session["summary"] = user_msg
            session["category"] = _infer_category(user_msg)
            session["current_state"] = "COLLECTING_DESCRIPTION"
            reply = "Got it. Please provide **more details**, including what happens and when it started."

    elif current_state == "COLLECTING_DESCRIPTION":
        if not user_msg:
            reply = "Please provide a description of the issue."
        elif len(user_msg) > MAX_DESCRIPTION_LENGTH:
            reply = f"Please keep the description to {MAX_DESCRIPTION_LENGTH} characters or fewer."
        else:
            session["description"] = user_msg
            session["priority"] = _infer_priority(
                f"{user_msg} {session.get('summary') or ''}"
            )
            session["category"] = session.get("category") or _infer_category(
                f"{session.get('summary') or ''} {user_msg}"
            )
            session["current_state"] = "CONFIRMING"
            reply = _draft(session)

    elif current_state == "EDITING_FIELD":
        field = session.get("editing_field")
        if field not in {"email", "summary", "description", "category", "priority"}:
            session["current_state"] = "CONFIRMING"
            reply = _draft(session, "I lost track of that edit. Here is the current draft:")
        else:
            error = _apply_change(session, field, user_msg)
            if error:
                reply = f"{error} Please enter a new **{field}**."
            else:
                session["editing_field"] = None
                session["current_state"] = "CONFIRMING"
                reply = _draft(session, f"Updated **{field}**. Here is the revised ticket:")

    elif current_state == "CONFIRMING":
        lowered = user_msg.lower()
        if lowered in YES_RESPONSES:
            try:
                result = create_ticket.invoke(
                    {
                        "email": session["email"],
                        "summary": session["summary"],
                        "description": session["description"],
                        "category": session.get("category") or "General",
                        "priority": session.get("priority") or "medium",
                    }
                )
            except (ConfigurationError, JiraAPIError) as exc:
                logger.warning("Jira ticket creation failed: %s", exc)
                reply = (
                    f"I couldn't create the Jira ticket: {exc}\n\n"
                    "Your draft is still saved. Type **yes** to retry, change a field, or **cancel**."
                )
            except Exception:
                logger.exception("Unexpected ticket creation error")
                reply = (
                    "I couldn't create the Jira ticket because of an unexpected service error. "
                    "Your draft is still saved; please retry or cancel."
                )
            else:
                match = JIRA_KEY_RE.search(result)
                history = list(session.get("ticket_history") or [])
                if match and match.group(0) not in history:
                    history.append(match.group(0))
                session["ticket_history"] = history
                _clear_ticket_fields(session)
                session["current_state"] = "DONE"
                reply = result
        elif lowered in NO_RESPONSES:
            _clear_ticket_fields(session)
            session["current_state"] = "GREETING"
            reply = "Ticket cancelled. Nothing was submitted to Jira."
        else:
            field = _requested_field(user_msg)
            if field:
                inline = _inline_value(user_msg, field)
                if inline:
                    error = _apply_change(session, field, inline)
                    reply = error or _draft(session, f"Updated **{field}**. Here is the revised ticket:")
                else:
                    session["editing_field"] = field
                    session["current_state"] = "EDITING_FIELD"
                    reply = f"Please enter the new **{field}**."
            else:
                reply = (
                    "Please type **yes** to submit, **cancel** to stop, or specify a field "
                    "to change: email, summary, description, category, or priority."
                )
    else:
        _clear_ticket_fields(session)
        session["current_state"] = "GREETING"
        reply = "The ticket flow was reset safely. Please tell me what you need help with."

    return _response(state, session, reply)
