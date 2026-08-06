from config import JiraSettings
from tools.jira_client import JiraAPIError, JiraClient, _adf_to_text


class FakeResponse:
    def __init__(self, status_code=200, payload=None, headers=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.headers = headers or {}
        self.text = text

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.responses.pop(0)


def _settings():
    return JiraSettings(
        base_url="https://example.atlassian.net",
        email="agent@example.com",
        api_token="secret-token",
        project_key="HELP",
        issue_type="Task",
        request_timeout_seconds=5,
    )


def test_jira_create_issue_builds_cloud_payload():
    session = FakeSession([FakeResponse(201, {"key": "HELP-7"})])
    client = JiraClient(_settings(), session=session)
    issue = client.create_issue(
        summary="VPN failure",
        description="Cannot connect",
        category="IT Support",
        priority="high",
    )
    assert issue == {
        "key": "HELP-7",
        "url": "https://example.atlassian.net/browse/HELP-7",
    }
    method, url, kwargs = session.calls[0]
    assert method == "POST"
    assert url.endswith("/rest/api/3/issue")
    fields = kwargs["json"]["fields"]
    assert fields["project"] == {"key": "HELP"}
    assert fields["priority"] == {"name": "High"}
    assert fields["description"]["type"] == "doc"


def test_jira_retries_temporary_failures(monkeypatch):
    session = FakeSession(
        [
            FakeResponse(503, {"errorMessages": ["busy"]}),
            FakeResponse(503, {"errorMessages": ["busy"]}),
            FakeResponse(503, {"errorMessages": ["busy"]}),
            FakeResponse(200, {"ok": True}),
        ]
    )
    sleeps = []
    monkeypatch.setattr("tools.jira_client.time.sleep", sleeps.append)
    response = JiraClient(_settings(), session=session)._request("GET", "/test")
    assert response.status_code == 200
    assert sleeps == [1, 2, 4]
    assert len(session.calls) == 4


def test_jira_raises_after_non_retryable_error():
    client = JiraClient(
        _settings(),
        session=FakeSession([FakeResponse(401, {"errorMessages": ["Unauthorized"]})]),
    )
    try:
        client._request("GET", "/test")
    except JiraAPIError as exc:
        assert exc.status_code == 401
        assert "401" in str(exc)
    else:
        raise AssertionError("Expected JiraAPIError")


def test_adf_comments_are_flattened():
    body = {
        "type": "doc",
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": "Working"}]},
            {"type": "paragraph", "content": [{"type": "text", "text": "on it"}]},
        ],
    }
    assert _adf_to_text(body) == "Working on it"


def test_create_and_status_tools_use_mapping_store(tmp_path, monkeypatch):
    import tools.create_ticket as create_module
    import tools.get_ticket_status as status_module
    import tools.ticket_store as store

    monkeypatch.setattr(store, "DB_PATH", tmp_path / "tickets.db")

    class FakeJira:
        def create_issue(self, **_):
            return {"key": "HELP-9", "url": "https://jira.test/browse/HELP-9"}

        def get_issue(self, key):
            return {
                "key": key,
                "url": f"https://jira.test/browse/{key}",
                "summary": "VPN failure",
                "status": "In Progress",
                "priority": "High",
                "assignee": "Alex",
                "latest_comment": "Investigating",
            }

    fake = FakeJira()
    monkeypatch.setattr(create_module, "_get_jira_client", lambda: fake)
    monkeypatch.setattr(status_module, "_get_jira_client", lambda: fake)
    result = create_module.create_ticket.invoke(
        {
            "email": "Person@Example.com",
            "summary": "VPN failure",
            "description": "Cannot connect",
            "category": "IT",
            "priority": "high",
        }
    )
    assert "HELP-9" in result
    mappings = store.get_ticket_mappings("person@example.com")
    assert [mapping["jira_key"] for mapping in mappings] == ["HELP-9"]

    status = status_module.get_ticket_status.invoke({"email": "person@example.com"})
    assert "In Progress" in status
    assert "Alex" in status
    assert "Investigating" in status
