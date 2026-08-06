"""IT sub-agent: retrieve, answer from context, or offer a Jira escalation."""
from __future__ import annotations

import logging

from langchain_core.messages import AIMessage

from agent.it_agent.prompts import IT_SYSTEM_PROMPT
from memory.session import update_activity
from rag.confidence import confidence_gate

logger = logging.getLogger(__name__)


def run_it_agent(state: dict) -> dict:
    query = state["messages"][-1].content
    session = update_activity(dict(state.get("session") or {}))
    prompt = IT_SYSTEM_PROMPT.format(
        email=session.get("email") or "not provided",
        current_state=session.get("current_state", "GREETING"),
    )
    try:
        answer, action = confidence_gate(
            query,
            domain="it",
            system_prompt=prompt,
        )
    except Exception:
        logger.exception("IT retrieval pipeline failed")
        reply = (
            "The IT knowledge service is temporarily unavailable, so I can't safely answer "
            "that question right now. Please try again shortly."
        )
    else:
        if action == "answer":
            reply = answer
            session["current_state"] = "GREETING"
        else:
            reply = (
                "I don't have enough information about that in our IT knowledge base. "
                "Would you like me to create a Jira support ticket for the IT team?"
            )
            session.update(
                {
                    "current_state": "ESCALATION_CONFIRMING",
                    "summary": query,
                    "category": "IT",
                }
            )
    return {
        "messages": [AIMessage(content=reply)],
        "session": session,
        "intent": state.get("intent", "rag_it"),
    }
