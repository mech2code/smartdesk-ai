"""LLM intent classification with a deterministic fallback."""
from __future__ import annotations

import json
import logging
from functools import lru_cache

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from config import get_app_settings, validate_openai

logger = logging.getLogger(__name__)

ALLOWED_INTENTS = {"rag_it", "rag_hr", "ticket_create", "ticket_status", "ambiguous"}
TICKET_STATES = {
    "ESCALATION_CONFIRMING",
    "COLLECTING_EMAIL",
    "COLLECTING_SUMMARY",
    "COLLECTING_DESCRIPTION",
    "CONFIRMING",
    "EDITING_FIELD",
}
STATUS_STATES = {"STATUS_COLLECTING_EMAIL"}

SYSTEM = """Classify the user's message into exactly one intent:
rag_it, rag_hr, ticket_create, ticket_status, ambiguous.

rag_it: IT questions about VPN, passwords, MFA, software, email, Wi-Fi, or hardware.
rag_hr: HR questions about benefits, leave, policies, payroll, performance, or remote work.
ticket_create: the user explicitly wants to create or report a support issue.
ticket_status: the user wants to check an existing ticket.
ambiguous: the request is unclear.

Return JSON only: {"intent":"...","clarification":"..."}. Include clarification only
for ambiguous requests."""


@lru_cache(maxsize=1)
def _get_llm() -> ChatOpenAI:
    validate_openai()
    return ChatOpenAI(
        model=get_app_settings().openai_chat_model,
        temperature=0,
        timeout=30,
        max_retries=2,
    )


def _fallback_intent(message: str) -> dict[str, str]:
    text = message.lower()
    if any(term in text for term in ("ticket status", "check my ticket", "existing ticket", "status of")):
        return {"intent": "ticket_status"}
    if any(term in text for term in ("create a ticket", "open a ticket", "raise a ticket", "report an issue")):
        return {"intent": "ticket_create"}
    if any(term in text for term in ("leave", "benefit", "payroll", "salary", "performance", "remote work", "hr policy")):
        return {"intent": "rag_hr"}
    if any(term in text for term in ("vpn", "password", "mfa", "wi-fi", "wifi", "software", "laptop", "printer", "email setup")):
        return {"intent": "rag_it"}
    return {
        "intent": "ambiguous",
        "clarification": "Could you clarify whether you need IT help, HR information, a new ticket, or a ticket-status check?",
    }


def _parse_response(content: str, original_message: str) -> dict[str, str]:
    cleaned = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        parsed = json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        return _fallback_intent(original_message)
    if parsed.get("intent") not in ALLOWED_INTENTS:
        return _fallback_intent(original_message)
    return parsed


def detect_intent(state: dict) -> dict:
    session = state.get("session") or {}
    current_state = session.get("current_state", "GREETING")
    if current_state in TICKET_STATES:
        return {"intent": "ticket_create"}
    if current_state in STATUS_STATES:
        return {"intent": "ticket_status"}

    last_msg = state["messages"][-1].content
    try:
        response = _get_llm().invoke(
            [SystemMessage(content=SYSTEM), HumanMessage(content=last_msg)]
        )
        parsed = _parse_response(response.content, last_msg)
    except Exception as exc:  # fallback keeps non-RAG flows usable during LLM outages
        logger.warning("Intent model unavailable; using keyword fallback: %s", exc)
        parsed = _fallback_intent(last_msg)

    intent = parsed["intent"]
    update: dict = {"intent": intent}
    if intent == "ambiguous":
        update["messages"] = [
            AIMessage(
                content=parsed.get(
                    "clarification", "Could you clarify what you need help with?"
                )
            )
        ]
    return update

