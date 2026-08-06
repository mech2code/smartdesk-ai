"""Create empty SmartDesk Qdrant collections without indexing documents."""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from config import get_app_settings

COLLECTIONS = ("it_kb", "hr_kb")


def main() -> None:
    settings = get_app_settings()
    client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port, timeout=10)
    existing = {collection.name for collection in client.get_collections().collections}
    for name in COLLECTIONS:
        if name in existing:
            print(f"  {name} already exists — skipping")
            continue
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=settings.openai_embedding_dimensions,
                distance=Distance.COSINE,
            ),
        )
        print(f"  {name} created")


if __name__ == "__main__":
    main()
