"""Top-level LangGraph orchestration for all SmartDesk flows."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from agent.hr_agent.graph import run_hr_agent
from agent.intent_detector import detect_intent
from agent.it_agent.graph import run_it_agent
from agent.router import route
from agent.status_flow import run_status_flow
from agent.ticket_flow import run_ticket_flow


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    session: dict
    intent: str | None


def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("intent_detector", detect_intent)
    builder.add_node("it_agent", run_it_agent)
    builder.add_node("hr_agent", run_hr_agent)
    builder.add_node("ticket_flow", run_ticket_flow)
    builder.add_node("status_flow", run_status_flow)
    builder.set_entry_point("intent_detector")

    builder.add_conditional_edges(
        "intent_detector",
        route,
        {
            "it_agent": "it_agent",
            "hr_agent": "hr_agent",
            "ticket_flow": "ticket_flow",
            "status_flow": "status_flow",
            END: END,
        },
    )
    for node in ("it_agent", "hr_agent", "ticket_flow", "status_flow"):
        builder.add_edge(node, END)
    return builder.compile(checkpointer=MemorySaver())

