"""Validate SmartDesk configuration and optionally test live dependencies."""
from __future__ import annotations

import argparse
import sys

import requests

from config import ConfigurationError, get_app_settings, get_jira_settings, validate_openai
from tools.jira_client import JiraAPIError, JiraClient


def _pass(label: str) -> None:
    print(f"PASS  {label}")


def _fail(label: str, error: Exception | str) -> None:
    print(f"FAIL  {label}: {error}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check SmartDesk environment and services")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Validate configuration without contacting Qdrant or Jira",
    )
    args = parser.parse_args()
    failures = 0

    try:
        validate_openai()
        _pass("OPENAI_API_KEY is configured")
    except ConfigurationError as exc:
        failures += 1
        _fail("OpenAI configuration", exc)

    try:
        settings = get_app_settings()
        jira_settings = get_jira_settings()
        _pass("Application and Jira settings are valid")
    except ConfigurationError as exc:
        failures += 1
        _fail("Application configuration", exc)
        return failures

    if not args.offline:
        try:
            response = requests.get(
                f"http://{settings.qdrant_host}:{settings.qdrant_port}/collections",
                timeout=5,
            )
            response.raise_for_status()
            _pass("Qdrant is reachable")
        except requests.RequestException as exc:
            failures += 1
            _fail("Qdrant connection", exc)

        try:
            JiraClient(jira_settings)._request(
                "GET", "/rest/api/3/myself", max_retries=0
            )
            _pass("Jira credentials are valid")
        except JiraAPIError as exc:
            failures += 1
            _fail("Jira connection", exc)

    if failures:
        print(f"\n{failures} setup check(s) failed.")
        return 1
    print("\nSmartDesk setup checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

