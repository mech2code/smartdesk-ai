from types import SimpleNamespace

from langchain_core.messages import HumanMessage

from agent.ticket_flow import run_ticket_flow
from memory.session import new_session


def _state(content: str, session: dict) -> dict:
    return {
        "messages": [HumanMessage(content=content)],
        "session": session,
        "intent": "ticket_create",
    }


def _run(content: str, session: dict) -> tuple[dict, str]:
    result = run_ticket_flow(_state(content, session))
    assert len(result["messages"]) == 1  # nodes return only the new message
    return result["session"], result["messages"][0].content


def test_new_ticket_reuses_known_email():
    session = new_session(email="user@example.com")
    session, reply = _run("Create a ticket", session)
    assert session["current_state"] == "COLLECTING_SUMMARY"
    assert "what is the issue" in reply.lower()


def test_invalid_email_stays_in_email_state():
    session = new_session()
    session, _ = _run("Create a ticket", session)
    session, reply = _run("not-an-email", session)
    assert session["current_state"] == "COLLECTING_EMAIL"
    assert session["email"] is None
    assert "valid" in reply.lower()


def test_rag_escalation_requires_yes():
    session = new_session()
    session.update(
        {
            "current_state": "ESCALATION_CONFIRMING",
            "summary": "Unknown monitor issue",
            "category": "IT",
        }
    )
    session, reply = _run("no", session)
    assert session["current_state"] == "GREETING"
    assert session["summary"] is None
    assert "not created" in reply.lower()


def test_rag_escalation_yes_preserves_summary():
    session = new_session(email="user@example.com")
    session.update(
        {
            "current_state": "ESCALATION_CONFIRMING",
            "summary": "Unknown monitor issue",
            "category": "IT",
        }
    )
    session, _ = _run("yes", session)
    assert session["current_state"] == "COLLECTING_DESCRIPTION"
    assert session["summary"] == "Unknown monitor issue"


def test_all_ticket_fields_can_be_corrected():
    session = new_session(email="old@example.com")
    session.update(
        {
            "current_state": "CONFIRMING",
            "summary": "Old summary",
            "description": "Old description",
            "category": "IT",
            "priority": "medium",
        }
    )
    changes = [
        ("change email to new@example.com", "email", "new@example.com"),
        ("change summary to Payroll question", "summary", "Payroll question"),
        ("change description to The deduction is incorrect", "description", "The deduction is incorrect"),
        ("change category to HR", "category", "HR"),
        ("change priority to high", "priority", "high"),
    ]
    for command, field, expected in changes:
        session, reply = _run(command, session)
        assert session[field] == expected
        assert session["current_state"] == "CONFIRMING"
        assert "revised ticket" in reply.lower()


def test_full_ticket_flow_calls_confirmed_tool(monkeypatch):
    import agent.ticket_flow as ticket_flow

    captured = {}

    def fake_invoke(payload):
        captured.update(payload)
        return "Ticket created successfully!\n- **Ticket ID**: [HELP-42](https://jira.test/browse/HELP-42)"

    monkeypatch.setattr(ticket_flow, "create_ticket", SimpleNamespace(invoke=fake_invoke))
    session = new_session()
    for message in (
        "Create a ticket",
        "person@example.com",
        "VPN disconnects",
        "It disconnects every ten minutes and is blocking my work",
        "yes",
    ):
        session, reply = _run(message, session)

    assert captured["email"] == "person@example.com"
    assert captured["category"] == "IT"
    assert captured["priority"] == "high"
    assert session["current_state"] == "DONE"
    assert session["ticket_history"] == ["HELP-42"]
    assert session["summary"] is None
    assert "HELP-42" in reply


def test_cancel_does_not_call_jira(monkeypatch):
    import agent.ticket_flow as ticket_flow

    def should_not_run(_):
        raise AssertionError("Jira must not be called when the user cancels")

    monkeypatch.setattr(ticket_flow, "create_ticket", SimpleNamespace(invoke=should_not_run))
    session = new_session(email="person@example.com")
    session.update(
        {
            "current_state": "CONFIRMING",
            "summary": "Test",
            "description": "Details",
            "category": "IT",
            "priority": "medium",
        }
    )
    session, reply = _run("cancel", session)
    assert session["current_state"] == "GREETING"
    assert "nothing was submitted" in reply.lower()
