"""Small Jira Cloud REST client used by SmartDesk ticket tools."""
from __future__ import annotations

import re
import time
from typing import Any

import requests

from config import JiraSettings, get_jira_settings


class JiraAPIError(RuntimeError):
    """A Jira request failed or returned an invalid response."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _text_to_adf(text: str) -> dict[str, Any]:
    """Convert plain text into the Atlassian Document Format Jira Cloud expects."""
    paragraphs = []
    for line in text.splitlines() or [text]:
        content = [{"type": "text", "text": line}] if line else []
        paragraphs.append({"type": "paragraph", "content": content})
    return {"type": "doc", "version": 1, "content": paragraphs}


def _adf_to_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(filter(None, (_adf_to_text(item) for item in value))).strip()
    if isinstance(value, dict):
        own_text = value.get("text", "")
        child_text = _adf_to_text(value.get("content", []))
        return " ".join(part for part in (own_text, child_text) if part).strip()
    return ""


def _safe_label(category: str) -> str:
    label = re.sub(r"[^a-z0-9_-]+", "-", category.lower()).strip("-")
    return label or "general"


class JiraClient:
    RETRYABLE_STATUS_CODES = {429, 502, 503, 504}
    PRIORITY_NAMES = {
        "critical": "Highest",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
    }

    def __init__(
        self,
        settings: JiraSettings | None = None,
        session: requests.Session | None = None,
    ):
        self.settings = settings or get_jira_settings()
        self.session = session or requests.Session()

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict | None = None,
        params: dict | None = None,
        max_retries: int = 3,
    ) -> requests.Response:
        url = f"{self.settings.base_url}{path}"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        for attempt in range(max_retries + 1):
            try:
                response = self.session.request(
                    method,
                    url,
                    auth=(self.settings.email, self.settings.api_token),
                    headers=headers,
                    json=json_body,
                    params=params,
                    timeout=self.settings.request_timeout_seconds,
                )
            except requests.RequestException as exc:
                if attempt < max_retries:
                    time.sleep(2**attempt)
                    continue
                raise JiraAPIError("Could not connect to Jira after multiple attempts.") from exc

            if response.status_code in self.RETRYABLE_STATUS_CODES and attempt < max_retries:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after and retry_after.isdigit() else 2**attempt
                time.sleep(delay)
                continue

            if response.status_code >= 400:
                try:
                    payload = response.json()
                    if isinstance(payload, dict):
                        details = (
                            payload.get("errorMessages")
                            or payload.get("errors")
                            or payload
                        )
                    else:
                        details = payload
                except ValueError:
                    details = response.text[:300]
                raise JiraAPIError(
                    f"Jira returned HTTP {response.status_code}: {details}",
                    status_code=response.status_code,
                )

            return response

        raise JiraAPIError("Jira is unavailable after multiple attempts.")

    def create_issue(
        self,
        *,
        summary: str,
        description: str,
        category: str,
        priority: str,
    ) -> dict[str, str]:
        summary = summary.strip()
        description = description.strip()
        if not summary or len(summary) > 255:
            raise JiraAPIError("Ticket summary must contain between 1 and 255 characters.")
        if not description or len(description) > 5000:
            raise JiraAPIError("Ticket description must contain between 1 and 5000 characters.")
        fields = {
            "project": {"key": self.settings.project_key},
            "summary": summary,
            "description": _text_to_adf(description),
            "issuetype": {"name": self.settings.issue_type},
            "priority": {"name": self.PRIORITY_NAMES.get(priority.lower(), "Medium")},
            "labels": ["smartdesk-ai", _safe_label(category)],
        }
        response = self._request("POST", "/rest/api/3/issue", json_body={"fields": fields})
        try:
            payload = response.json()
            key = payload["key"]
        except (ValueError, KeyError, TypeError) as exc:
            raise JiraAPIError("Jira created an issue but did not return an issue key.") from exc
        return {"key": key, "url": f"{self.settings.base_url}/browse/{key}"}

    def get_issue(self, issue_key: str) -> dict[str, str]:
        response = self._request(
            "GET",
            f"/rest/api/3/issue/{issue_key}",
            params={
                "fields": "summary,status,priority,assignee,created,updated",
            },
        )
        try:
            payload = response.json()
            fields = payload["fields"]
        except (ValueError, KeyError, TypeError) as exc:
            raise JiraAPIError(f"Jira returned invalid data for {issue_key}.") from exc

        try:
            comment_response = self._request(
                "GET",
                f"/rest/api/3/issue/{issue_key}/comment",
                params={"orderBy": "-created", "maxResults": 1},
            )
            comments = (comment_response.json() or {}).get("comments") or []
        except (JiraAPIError, ValueError, TypeError, AttributeError):
            comments = []
        latest_comment = _adf_to_text(comments[-1].get("body")) if comments else "No comments"
        assignee = fields.get("assignee") or {}
        priority = fields.get("priority") or {}
        status = fields.get("status") or {}

        return {
            "key": payload.get("key", issue_key),
            "url": f"{self.settings.base_url}/browse/{issue_key}",
            "summary": fields.get("summary") or "No summary",
            "status": status.get("name") or "Unknown",
            "priority": priority.get("name") or "Unknown",
            "assignee": assignee.get("displayName") or "Unassigned",
            "latest_comment": latest_comment or "No comments",
            "created": fields.get("created") or "",
            "updated": fields.get("updated") or "",
        }
