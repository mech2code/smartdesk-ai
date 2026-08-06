"""Chainlit entry point for SmartDesk AI."""
from __future__ import annotations

import logging
import uuid

import chainlit as cl

from agent.orchestrator import build_graph
from memory.longterm import load_employee, merge_employee_memory, save_employee
from memory.session import new_session, session_is_expired

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
graph = build_graph()


def _hydrate_and_save(session: dict) -> dict:
    email = session.get("email")
    if not email:
        return session
    try:
        if not session.get("_ltm_loaded"):
            session = merge_employee_memory(session, load_employee(email))
        save_employee(email, session)
    except Exception:
        logger.exception("Could not hydrate or persist long-term employee memory")
    return session


@cl.on_chat_start
async def on_chat_start():
    session = new_session()
    session["_graph_thread_id"] = cl.context.session.id
    cl.user_session.set("session", session)
    await cl.Message(
        content=(
            "Hi! I'm SmartDesk AI, your IT and HR helpdesk assistant.\n\n"
            "I can answer IT and HR knowledge-base questions, create Jira support "
            "tickets after your confirmation, and check live Jira ticket status.\n\n"
            "How can I help you today?"
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    session = cl.user_session.get("session") or new_session()
    if session_is_expired(session):
        session = new_session(email=session.get("email"))
        session["_graph_thread_id"] = f"{cl.context.session.id}:{uuid.uuid4()}"
    thread_id = session.get("_graph_thread_id") or cl.context.session.id
    session["_graph_thread_id"] = thread_id

    try:
        result = await graph.ainvoke(
            {
                "messages": [{"role": "user", "content": message.content}],
                "session": session,
                "intent": None,
            },
            config={"configurable": {"thread_id": thread_id}},
        )
        updated_session = _hydrate_and_save(result.get("session", session))
        cl.user_session.set("session", updated_session)
        reply = result["messages"][-1].content
    except Exception:
        logger.exception("Unhandled SmartDesk message error")
        reply = (
            "I ran into an unexpected service error and did not submit any new ticket. "
            "Please try again, or contact the helpdesk directly if the problem continues."
        )
    await cl.Message(content=reply).send()


@cl.on_chat_end
def on_chat_end():
    session = cl.user_session.get("session")
    if session and session.get("email"):
        try:
            save_employee(session["email"], session)
        except Exception:
            logger.exception("Failed to persist employee memory at chat end")
