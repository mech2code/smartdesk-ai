from types import SimpleNamespace

from langchain_core.messages import HumanMessage

from agent.intent_detector import _fallback_intent, detect_intent
from agent.status_flow import run_status_flow
from memory.session import new_session


def test_keyword_fallback_covers_primary_flows():
    assert _fallback_intent("How do I reset my VPN?")["intent"] == "rag_it"
    assert _fallback_intent("What is the parental leave policy?")["intent"] == "rag_hr"
    assert _fallback_intent("Please create a ticket")["intent"] == "ticket_create"
    assert _fallback_intent("Check my ticket status")["intent"] == "ticket_status"


def test_mid_flow_intent_does_not_call_llm(monkeypatch):
    monkeypatch.setattr("agent.intent_detector._get_llm", lambda: (_ for _ in ()).throw(AssertionError()))
    state = {
        "messages": [HumanMessage(content="no")],
        "session": {"current_state": "ESCALATION_CONFIRMING"},
        "intent": None,
    }
    assert detect_intent(state) == {"intent": "ticket_create"}


def test_status_flow_collects_email_then_looks_up(monkeypatch):
    import agent.status_flow as status_flow

    monkeypatch.setattr(
        status_flow,
        "get_ticket_status",
        SimpleNamespace(invoke=lambda payload: f"Live Jira result for {payload['email']}"),
    )
    session = new_session()
    first = run_status_flow(
        {
            "messages": [HumanMessage(content="check status")],
            "session": session,
            "intent": "ticket_status",
        }
    )
    assert first["session"]["current_state"] == "STATUS_COLLECTING_EMAIL"
    assert len(first["messages"]) == 1

    second = run_status_flow(
        {
            "messages": [HumanMessage(content="user@example.com")],
            "session": first["session"],
            "intent": "ticket_status",
        }
    )
    assert second["session"]["current_state"] == "GREETING"
    assert "Live Jira result" in second["messages"][0].content
