"""Embedding pipeline using Sentence Transformers (local, CPU-based)."""

import logging
import uuid
from typing import Any

from sentence_transformers import SentenceTransformer

from app.core.qdrant import get_qdrant_client

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None
MODEL_NAME = "BAAI/bge-small-en-v1.5"


def get_embedding_model() -> SentenceTransformer:
    """Return a singleton embedding model instance (loaded once, reused)."""
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_text(text: str) -> list[float]:
    """Embed a single text string and return the vector as a list of floats."""
    model = get_embedding_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed multiple texts in batch and return vectors."""
    model = get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return [emb.tolist() for emb in embeddings]


def _get_qdrant_collection_name(doc_type: str) -> str:
    """Map document_type to Qdrant collection name."""
    doc_type_lower = doc_type.lower().replace(" ", "_")
    if doc_type_lower == "resume":
        return "resumes"
    elif doc_type_lower in ("job_description", "jd"):
        return "job_descriptions"
    else:
        return "hr_documents"


def _build_payload(
    chunk: dict, doc_type: str, client_id: str, auto_tags: dict | None
) -> dict:
    """Build Qdrant payload from chunk data."""
    payload: dict[str, Any] = {
        "doc_id": str(chunk["document_id"]),
        "chunk_index": chunk["chunk_index"],
        "client_id": client_id,
    }

    if doc_type == "resume":
        payload["candidate_name"] = (auto_tags or {}).get("candidate_name")
        payload["skills"] = (auto_tags or {}).get("skills", [])
        payload["experience_years"] = None
        payload["location"] = None
    elif doc_type in ("job_description", "jd"):
        payload["job_title"] = (auto_tags or {}).get("role")
        payload["department"] = None
        payload["location"] = None
    else:
        payload["doc_type"] = doc_type
        payload["tags"] = (auto_tags or {}).get("skills", [])

    return payload


async def embed_and_store_chunks(
    chunks: list[dict[str, Any]],
    doc_type: str,
    client_id: str,
    auto_tags: dict | None = None,
) -> list[uuid.UUID]:
    """Embed chunk texts and store vectors + payloads in Qdrant.
    Returns list of Qdrant point IDs.
    """
    texts = [c["chunk_text"] for c in chunks]
    vectors = embed_texts(texts)
    collection = _get_qdrant_collection_name(doc_type)

    client = get_qdrant_client()
    point_ids: list[uuid.UUID] = []
    points: list[dict] = []

    for chunk, vector in zip(chunks, vectors):
        point_id = uuid.uuid4()
        points.append(
            {
                "id": str(point_id),
                "vector": vector,
                "payload": _build_payload(chunk, doc_type, client_id, auto_tags),
            }
        )
        point_ids.append(point_id)

    # qdrant-client's stub types `points` as PointStruct objects, but the client
    # accepts plain dicts at runtime (pydantic-parses them); not worth the
    # PointStruct construction churn for this pass.
    client.upsert(collection_name=collection, points=points)  # type: ignore[arg-type]
    logger.info(f"Stored {len(points)} vectors in Qdrant collection '{collection}'")
    return point_ids
