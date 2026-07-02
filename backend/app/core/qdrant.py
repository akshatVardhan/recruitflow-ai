import logging

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http.models import (
    CollectionStatus,
    Distance,
    VectorParams,
)

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: QdrantClient | None = None

# Vector configuration
VECTOR_SIZE = 384  # BAAI/bge-small-en-v1.5 output dimension
DISTANCE = Distance.COSINE

# Collection definitions matching schema.md
COLLECTIONS = {
    "resumes": {
        "vector_size": VECTOR_SIZE,
        "distance": DISTANCE,
        "payload_schema": {
            "doc_id": PayloadSchemaType.KEYWORD,
            "chunk_index": PayloadSchemaType.INTEGER,
            "candidate_name": PayloadSchemaType.KEYWORD,
            "skills": PayloadSchemaType.LIST_KEYWORD,
            "experience_years": PayloadSchemaType.INTEGER,
            "location": PayloadSchemaType.KEYWORD,
            "client_id": PayloadSchemaType.KEYWORD,
        },
    },
    "job_descriptions": {
        "vector_size": VECTOR_SIZE,
        "distance": DISTANCE,
        "payload_schema": {
            "doc_id": PayloadSchemaType.KEYWORD,
            "chunk_index": PayloadSchemaType.INTEGER,
            "job_title": PayloadSchemaType.KEYWORD,
            "department": PayloadSchemaType.KEYWORD,
            "location": PayloadSchemaType.KEYWORD,
            "client_id": PayloadSchemaType.KEYWORD,
        },
    },
    "hr_documents": {
        "vector_size": VECTOR_SIZE,
        "distance": DISTANCE,
        "payload_schema": {
            "doc_id": PayloadSchemaType.KEYWORD,
            "chunk_index": PayloadSchemaType.INTEGER,
            "doc_type": PayloadSchemaType.KEYWORD,
            "tags": PayloadSchemaType.LIST_KEYWORD,
            "client_id": PayloadSchemaType.KEYWORD,
        },
    },
}


def get_qdrant_client() -> QdrantClient:
    """Return a singleton QdrantClient instance."""
    global _client
    if _client is not None:
        return _client
    _client = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key or None,
    )
    return _client


async def ensure_collections() -> dict[str, str]:
    """Idempotent: create all 3 collections if they do not exist.
    Returns a dict mapping collection name to its status.
    """
    client = get_qdrant_client()
    results: dict[str, str] = {}

    for collection_name, config in COLLECTIONS.items():
        try:
            existing = client.get_collection(collection_name)
            if existing.status == CollectionStatus.GREEN:
                results[collection_name] = "exists"
                continue
        except (UnexpectedResponse, ValueError):
            pass

        try:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=config["vector_size"],
                    distance=config["distance"],
                ),
            )

            # Create payload indexes for all fields
            for field_name, field_type in config["payload_schema"].items():
                client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field_name,
                    field_schema=field_type,
                )

            logger.info(f"Created Qdrant collection: {collection_name}")
            results[collection_name] = "created"
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            results[collection_name] = f"error: {e}"

    return results


async def get_collections_status() -> dict[str, dict]:
    """Return status info for all configured collections."""
    client = get_qdrant_client()
    status: dict[str, dict] = {}

    for collection_name in COLLECTIONS:
        try:
            info = client.get_collection(collection_name)
            status[collection_name] = {
                "exists": True,
                "status": info.status.name if info.status else "unknown",
                "vectors_count": info.vectors_count if hasattr(info, "vectors_count") else 0,
                "points_count": info.points_count if hasattr(info, "points_count") else 0,
            }
        except (UnexpectedResponse, ValueError):
            status[collection_name] = {
                "exists": False,
                "status": "not_found",
            }

    return status
