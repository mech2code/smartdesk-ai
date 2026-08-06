"""Test-suite safety settings."""

import os

# Unit tests mock external services and must never submit LangSmith traces.
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGSMITH_TRACING"] = "false"
