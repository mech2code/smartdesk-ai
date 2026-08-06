"""Index knowledge-base Markdown into deterministic Qdrant collections."""
from __future__ import annotations

import argparse
import re
import uuid
from functools import lru_cache
from pathlib import Path

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from config import get_app_settings, validate_openai

CHUNK_TOKENS = 500
OVERLAP_TOKENS = 75
KB_ROOT = Path(__file__).parent.parent / "kb"
DOMAIN_COLLECTIONS = {"it": "it_kb", "hr": "hr_kb"}


@lru_cache(maxsize=1)
def _get_openai_client() -> OpenAI:
    validate_openai()
    return OpenAI()


@lru_cache(maxsize=1)
def _get_qdrant_client() -> QdrantClient:
    settings = get_app_settings()
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port, timeout=30)


def _ensure_collection(name: str, *, recreate: bool) -> None:
    client = _get_qdrant_client()
    existing = {collection.name for collection in client.get_collections().collections}
    if recreate and name in existing:
        client.delete_collection(name)
        existing.remove(name)
    if name not in existing:
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=get_app_settings().openai_embedding_dimensions,
                distance=Distance.COSINE,
            ),
        )
        print(f"  Created collection: {name}")


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _chunk_text(text: str, source: str) -> list[dict]:
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n{2,}", text) if paragraph.strip()]
    chunks: list[dict] = []
    current: list[str] = []
    current_tokens = 0

    for paragraph in paragraphs:
        paragraph_tokens = _approx_tokens(paragraph)
        if current and current_tokens + paragraph_tokens > CHUNK_TOKENS:
            chunks.append(
                {"text": "\n\n".join(current), "chunk_id": len(chunks), "source": source}
            )
            overlap: list[str] = []
            overlap_tokens = 0
            for prior in reversed(current):
                prior_tokens = _approx_tokens(prior)
                if overlap_tokens + prior_tokens > OVERLAP_TOKENS:
                    break
                overlap.insert(0, prior)
                overlap_tokens += prior_tokens
            current = overlap
            current_tokens = overlap_tokens
        current.append(paragraph)
        current_tokens += paragraph_tokens

    if current:
        chunks.append(
            {"text": "\n\n".join(current), "chunk_id": len(chunks), "source": source}
        )
    return chunks


def _embed_batch(texts: list[str]) -> list[list[float]]:
    settings = get_app_settings()
    response = _get_openai_client().embeddings.create(
        model=settings.openai_embedding_model,
        dimensions=settings.openai_embedding_dimensions,
        input=texts,
    )
    return [item.embedding for item in response.data]


def _point_id(domain: str, source: str, chunk_id: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"smartdesk:{domain}:{source}:{chunk_id}"))


def index_domain(domain: str, *, recreate: bool = True) -> int:
    if domain not in DOMAIN_COLLECTIONS:
        raise ValueError("domain must be 'it' or 'hr'")
    collection = DOMAIN_COLLECTIONS[domain]
    _ensure_collection(collection, recreate=recreate)
    markdown_files = sorted((KB_ROOT / domain).glob("*.md"))
    if not markdown_files:
        print(f"  No Markdown files found for {domain}")
        return 0

    chunks: list[dict] = []
    for markdown_file in markdown_files:
        file_chunks = _chunk_text(
            markdown_file.read_text(encoding="utf-8"), source=markdown_file.name
        )
        for chunk in file_chunks:
            chunk.update(
                {
                    "domain": domain,
                    "category": markdown_file.stem.replace("_", " "),
                }
            )
        chunks.extend(file_chunks)
        print(f"  {markdown_file.name}: {len(file_chunks)} chunks")

    client = _get_qdrant_client()
    batch_size = 100
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        embeddings = _embed_batch([chunk["text"] for chunk in batch])
        points = [
            PointStruct(
                id=_point_id(domain, chunk["source"], chunk["chunk_id"]),
                vector=vector,
                payload=chunk,
            )
            for chunk, vector in zip(batch, embeddings)
        ]
        client.upsert(collection_name=collection, points=points, wait=True)
        print(f"  Uploaded batch {start // batch_size + 1}")
    print(f"  Indexed {len(chunks)} chunks into {collection}")
    return len(chunks)


def main() -> None:
    parser = argparse.ArgumentParser(description="Index SmartDesk knowledge-base documents")
    parser.add_argument("--domain", choices=["it", "hr", "all"], default="all")
    parser.add_argument(
        "--keep-collection",
        action="store_true",
        help="Upsert without recreating the collection (may retain removed chunks)",
    )
    args = parser.parse_args()
    domains = ["it", "hr"] if args.domain == "all" else [args.domain]
    for domain in domains:
        print(f"\nIndexing {domain.upper()} knowledge base...")
        index_domain(domain, recreate=not args.keep_collection)
    print("\nIndexing complete.")


if __name__ == "__main__":
    main()
