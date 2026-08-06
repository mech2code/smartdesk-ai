"""Environment-backed settings and startup validation for SmartDesk AI."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class ConfigurationError(RuntimeError):
    """Raised when required application configuration is missing or invalid."""


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigurationError(f"Missing required environment variable: {name}")
    return value


def _as_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer, got {raw!r}") from exc


def _as_float(name: str, default: float) -> float:
    raw = os.getenv(name, str(default))
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be a number, got {raw!r}") from exc


def _jira_base_url() -> str:
    value = _required("JIRA_BASE_URL").rstrip("/")
    if not value.startswith(("https://", "http://")):
        raise ConfigurationError("JIRA_BASE_URL must begin with https:// or http://")
    return value


@dataclass(frozen=True)
class AppSettings:
    openai_chat_model: str
    openai_embedding_model: str
    openai_embedding_dimensions: int
    qdrant_host: str
    qdrant_port: int
    confidence_threshold_it: float
    confidence_threshold_hr: float
    session_timeout_minutes: int


@dataclass(frozen=True)
class JiraSettings:
    base_url: str
    email: str
    api_token: str
    project_key: str
    issue_type: str
    request_timeout_seconds: int


@lru_cache(maxsize=1)
def get_app_settings() -> AppSettings:
    return AppSettings(
        openai_chat_model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o").strip() or "gpt-4o",
        openai_embedding_model=os.getenv(
            "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
        ).strip()
        or "text-embedding-3-small",
        openai_embedding_dimensions=_as_int("OPENAI_EMBEDDING_DIMENSIONS", 1536),
        qdrant_host=os.getenv("QDRANT_HOST", "localhost").strip() or "localhost",
        qdrant_port=_as_int("QDRANT_PORT", 6333),
        confidence_threshold_it=_as_float("CONFIDENCE_THRESHOLD_IT", 0.75),
        confidence_threshold_hr=_as_float("CONFIDENCE_THRESHOLD_HR", 0.72),
        session_timeout_minutes=_as_int("SESSION_TIMEOUT_MINUTES", 30),
    )


@lru_cache(maxsize=1)
def get_jira_settings() -> JiraSettings:
    return JiraSettings(
        base_url=_jira_base_url(),
        email=_required("JIRA_EMAIL"),
        api_token=_required("JIRA_API_TOKEN"),
        project_key=_required("JIRA_PROJECT_KEY"),
        issue_type=os.getenv("JIRA_ISSUE_TYPE", "Task").strip() or "Task",
        request_timeout_seconds=_as_int("JIRA_REQUEST_TIMEOUT_SECONDS", 20),
    )


def validate_openai() -> None:
    _required("OPENAI_API_KEY")


def clear_settings_cache() -> None:
    """Clear cached settings; useful after changing environment variables in tests."""
    get_app_settings.cache_clear()
    get_jira_settings.cache_clear()
