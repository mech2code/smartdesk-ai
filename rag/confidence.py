"""Hybrid confidence gate with grounded generation and semantic caching."""
from __future__ import annotations

from functools import lru_cache

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from cache.semantic_cache import cache_lookup, cache_store
from config import get_app_settings, validate_openai
from rag.retriever import hybrid_search

INSUFFICIENT_RESPONSE = "I don't have enough information about that in our knowledge base."
DEFAULT_SYSTEM_PROMPT = """You are SmartDesk AI, an internal IT and HR helpdesk assistant.
Answer only from the supplied knowledge-base passages. If the passages are insufficient,
respond exactly: "I don't have enough information about that in our knowledge base."
Do not use outside knowledge. Cite supporting filenames using [Source: filename]."""


@lru_cache(maxsize=1)
def _get_llm() -> ChatOpenAI:
    validate_openai()
    return ChatOpenAI(
        model=get_app_settings().openai_chat_model,
        temperature=0,
        timeout=45,
        max_retries=2,
    )


def confidence_gate(
    query: str,
    domain: str,
    *,
    system_prompt: str | None = None,
    retrieval: tuple[list[str], float] | None = None,
    use_cache: bool = True,
) -> tuple[str | None, str]:
    """Return ``(answer, action)`` where action is ``answer`` or ``escalate``."""
    if domain not in {"it", "hr"}:
        raise ValueError("domain must be 'it' or 'hr'")

    if use_cache:
        cached = cache_lookup(query, domain)
        if cached:
            return cached, "answer"

    settings = get_app_settings()
    threshold = (
        settings.confidence_threshold_it
        if domain == "it"
        else settings.confidence_threshold_hr
    )
    chunks, score = retrieval if retrieval is not None else hybrid_search(query, domain)
    if not chunks or score < threshold:
        return None, "escalate"

    grounding = (system_prompt or DEFAULT_SYSTEM_PROMPT).strip()
    grounding += (
        "\n\nUse only the context below. Include [Source: filename] citations for factual claims. "
        f"If context is insufficient, respond exactly: {INSUFFICIENT_RESPONSE}"
    )
    context = "\n\n---\n\n".join(chunks)
    prompt = f"Context:\n{context}\n\nQuestion: {query}"
    response = _get_llm().invoke(
        [SystemMessage(content=grounding), HumanMessage(content=prompt)]
    )
    answer = response.content.strip()
    if "don't have enough information" in answer.lower():
        return None, "escalate"
    if use_cache:
        cache_store(query, answer, domain)
    return answer, "answer"
