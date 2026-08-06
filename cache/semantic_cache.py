"""Bounded, thread-safe semantic cache for grounded RAG answers."""
from __future__ import annotations

import math
import threading
from functools import lru_cache

from openai import OpenAI

from config import get_app_settings, validate_openai

SIMILARITY_THRESHOLD = 0.85
MAX_CACHE_ENTRIES = 256
_cache: list[dict] = []
_lock = threading.RLock()


@lru_cache(maxsize=1)
def _get_openai_client() -> OpenAI:
    validate_openai()
    return OpenAI()


def _embed(text: str) -> list[float]:
    settings = get_app_settings()
    response = _get_openai_client().embeddings.create(
        model=settings.openai_embedding_model,
        dimensions=settings.openai_embedding_dimensions,
        input=[text],
    )
    return response.data[0].embedding


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def cache_lookup(query: str, domain: str = "") -> str | None:
    """Return a cached answer for a semantically similar query in the same domain."""
    with _lock:
        candidates = [entry for entry in _cache if entry["domain"] == domain]
    if not candidates:
        return None
    query_vec = _embed(query)
    best = max(
        candidates,
        key=lambda entry: _cosine_similarity(query_vec, entry["embedding"]),
    )
    if _cosine_similarity(query_vec, best["embedding"]) >= SIMILARITY_THRESHOLD:
        return best["answer"]
    return None


def cache_store(query: str, answer: str, domain: str = "") -> None:
    """Store a grounded query-answer pair, evicting the oldest entry when full."""
    query_vec = _embed(query)
    with _lock:
        if len(_cache) >= MAX_CACHE_ENTRIES:
            _cache.pop(0)
        _cache.append(
            {
                "embedding": query_vec,
                "query": query,
                "answer": answer,
                "domain": domain,
            }
        )


def cache_clear() -> None:
    with _lock:
        _cache.clear()
