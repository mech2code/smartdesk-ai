from langgraph.graph import END

INTENT_TO_NODE = {
    "rag_it": "it_agent",
    "rag_hr": "hr_agent",
    "ticket_create": "ticket_flow",
    "ticket_status": "status_flow",
    "ambiguous": END,
}


def route(state: dict) -> str:
    """Return the name of the next node based on detected intent."""
    intent = state.get("intent", "ambiguous")
    return INTENT_TO_NODE.get(intent, END)
