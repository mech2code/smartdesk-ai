"""Dense + BM25 retrieval, reciprocal-rank fusion, and cross-encoder reranking."""
from __future__ import annotations

import math
from functools import lru_cache
from typing import TYPE_CHECKING

from openai import OpenAI
from qdrant_client import QdrantClient
from rank_bm25 import BM25Okapi

from config import get_app_settings, validate_openai

if TYPE_CHECKING:
    from sentence_transformers import CrossEncoder

TOP_K_DENSE = 20
TOP_K_BM25 = 20
TOP_K_RRF = 10
TOP_K_FINAL = 3
RRF_K = 60


class RetrievalError(RuntimeError):
    """The knowledge-base retrieval service could not complete a query."""


@lru_cache(maxsize=1)
def _get_openai_client() -> OpenAI:
    validate_openai()
    return OpenAI()


@lru_cache(maxsize=1)
def _get_qdrant_client() -> QdrantClient:
    settings = get_app_settings()
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port, timeout=10)


@lru_cache(maxsize=1)
def _get_cross_encoder() -> CrossEncoder:
    # Loading sentence-transformers also imports PyTorch. Keep that optional
    # during module import so utility functions and unit tests do not require
    # the local ML runtime until reranking is actually requested.
    from sentence_transformers import CrossEncoder

    return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


# domain -> (BM25 model or None, [{"id": point_id, "payload": payload}, ...])
_bm25_cache: dict[str, tuple[BM25Okapi | None, list[dict]]] = {}


def clear_bm25_cache() -> None:
    _bm25_cache.clear()


def _load_bm25(domain: str) -> tuple[BM25Okapi | None, list[dict]]:
    if domain not in _bm25_cache:
        client = _get_qdrant_client()
        collection = f"{domain}_kb"
        documents: list[dict] = []
        offset = None
        while True:
            results, offset = client.scroll(
                collection_name=collection,
                limit=200,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            documents.extend(
                {"id": str(point.id), "payload": point.payload or {}}
                for point in results
                if (point.payload or {}).get("text")
            )
            if offset is None:
                break
        tokenized = [doc["payload"]["text"].lower().split() for doc in documents]
        _bm25_cache[domain] = (BM25Okapi(tokenized) if tokenized else None, documents)
    return _bm25_cache[domain]


def _embed(text: str) -> list[float]:
    settings = get_app_settings()
    response = _get_openai_client().embeddings.create(
        model=settings.openai_embedding_model,
        dimensions=settings.openai_embedding_dimensions,
        input=[text],
    )
    return response.data[0].embedding


def _dense_search(collection: str, query_vector: list[float]):
    client = _get_qdrant_client()
    if hasattr(client, "query_points"):
        return client.query_points(
            collection_name=collection,
            query=query_vector,
            limit=TOP_K_DENSE,
            with_payload=True,
        ).points
    return client.search(
        collection_name=collection,
        query_vector=query_vector,
        limit=TOP_K_DENSE,
        with_payload=True,
    )


def _rrf_merge(dense_ids: list[str], bm25_ids: list[str]) -> list[str]:
    scores: dict[str, float] = {}
    for rank, doc_id in enumerate(dense_ids, start=1):
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (rank + RRF_K)
    for rank, doc_id in enumerate(bm25_ids, start=1):
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (rank + RRF_K)
    return sorted(scores, key=scores.get, reverse=True)[:TOP_K_RRF]


def _sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


def hybrid_search(query: str, domain: str) -> tuple[list[str], float]:
    """Return source-labelled top passages and the normalized best reranker score."""
    if domain not in {"it", "hr"}:
        raise ValueError("domain must be 'it' or 'hr'")
    collection = f"{domain}_kb"
    try:
        dense_results = _dense_search(collection, _embed(query))
        dense_payloads = {
            str(result.id): result.payload or {}
            for result in dense_results
            if (result.payload or {}).get("text")
        }
        dense_ids = list(dense_payloads)

        bm25, documents = _load_bm25(domain)
        bm25_payloads: dict[str, dict] = {}
        bm25_ids: list[str] = []
        if bm25 is not None:
            scores = bm25.get_scores(query.lower().split())
            ranked_indices = sorted(
                (index for index, score in enumerate(scores) if score > 0),
                key=lambda index: scores[index],
                reverse=True,
            )[:TOP_K_BM25]
            bm25_payloads = {
                documents[index]["id"]: documents[index]["payload"]
                for index in ranked_indices
            }
            bm25_ids = list(bm25_payloads)

        payloads = {**bm25_payloads, **dense_payloads}
        top_ids = _rrf_merge(dense_ids, bm25_ids)
        candidates = [payloads[doc_id] for doc_id in top_ids if doc_id in payloads]
        if not candidates:
            return [], 0.0

        pairs = [(query, payload["text"]) for payload in candidates]
        reranker_scores = _get_cross_encoder().predict(pairs)
        ranked = sorted(
            zip(reranker_scores, candidates, strict=True),
            key=lambda pair: pair[0],
            reverse=True,
        )
    except Exception as exc:
        raise RetrievalError(
            "The knowledge-base search service is unavailable. Check OpenAI, Qdrant, and the reranker model."
        ) from exc

    top_chunks = [
        f"[Source: {payload.get('source', 'unknown')}]\n{payload['text']}"
        for _, payload in ranked[:TOP_K_FINAL]
    ]
    best_score = float(ranked[0][0]) if ranked else 0.0
    return top_chunks, _sigmoid(best_score)
