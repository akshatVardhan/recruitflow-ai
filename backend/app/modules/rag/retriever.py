"""Hybrid retrieval: keyword (PostgreSQL FTS) + tag filter + semantic (Qdrant)."""

import logging
from typing import Any

from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.embeddings import embed_text
from app.core.qdrant import get_qdrant_client

logger = logging.getLogger(__name__)


async def keyword_search(
    db: AsyncSession,
    query: str,
    client_id: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """PostgreSQL full-text search on documents table.

    Uses the idx_documents_fts GIN index on title || extracted_text.
    """
    sql = text("""
        SELECT id, title, doc_type, file_name,
               ts_rank(to_tsvector('english', title || ' ' || coalesce(extracted_text, '')),
                       plainto_tsquery('english', :query)) AS rank,
               substring(extracted_text, 1, 300) AS preview
        FROM documents
        WHERE to_tsvector('english', title || ' ' || coalesce(extracted_text, ''))
              @@ plainto_tsquery('english', :query)
          AND client_id = :client_id
          AND deleted_at IS NULL
        ORDER BY rank DESC
        LIMIT :limit
    """)
    result = await db.execute(sql, {"query": query, "client_id": client_id, "limit": limit})
    rows = result.all()
    return [
        {
            "id": str(row.id),
            "title": row.title,
            "doc_type": row.doc_type,
            "file_name": row.file_name,
            "score": float(row.rank),
            "preview": row.preview,
            "source": "keyword",
        }
        for row in rows
    ]


def semantic_search(
    query: str,
    client_id: str,
    doc_type: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Qdrant vector similarity search with optional tag/type filter and mandatory client_id filter."""
    client = get_qdrant_client()
    query_vector = embed_text(query)

    # Determine which collection to search
    collections = ["resumes", "job_descriptions", "hr_documents"]
    if doc_type:
        if doc_type == "resume":
            collections = ["resumes"]
        elif doc_type in ("job_description", "jd"):
            collections = ["job_descriptions"]
        else:
            collections = ["hr_documents"]

    all_results: list[dict] = []
    for collection in collections:
        must_filters: list = [FieldCondition(key="client_id", match=MatchValue(value=client_id))]

        search_result = client.search(
            collection_name=collection,
            query_vector=query_vector,
            query_filter=Filter(must=must_filters),
            limit=limit,
            with_payload=True,
        )

        for scored_point in search_result:
            payload = scored_point.payload or {}
            all_results.append({
                "id": payload.get("doc_id", ""),
                "chunk_index": payload.get("chunk_index"),
                "score": float(scored_point.score),
                "source": f"semantic:{collection}",
                "payload": {k: v for k, v in payload.items() if k != "client_id"},
            })

    # Sort by score descending and limit
    all_results.sort(key=lambda x: x["score"], reverse=True)
    return all_results[:limit]


async def hybrid_search(
    db: AsyncSession,
    query: str,
    client_id: str,
    doc_type: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Hybrid search: keyword FTS + filtered semantic search, combined and re-ranked.

    Strategy: filter first by client_id, then re-rank by semantic score.
    """
    # Run both searches
    kw_results = await keyword_search(db, query, client_id, limit)
    sem_results = semantic_search(query, client_id, doc_type, limit)

    # Combine: interleave by score, deduplicate by document ID
    seen_docs: set[str] = set()
    combined: list[dict] = []

    # Semantic results first (higher precision)
    for r in sem_results:
        doc_id = r["id"]
        if doc_id not in seen_docs:
            seen_docs.add(doc_id)
            combined.append(r)

    # Keyword results for coverage
    for r in kw_results:
        doc_id = r["id"]
        if doc_id not in seen_docs:
            seen_docs.add(doc_id)
            combined.append(r)

    return {
        "query": query,
        "total": len(combined),
        "results": combined[:limit],
        "sources": {
            "keyword_count": len(kw_results),
            "semantic_count": len(sem_results),
        },
    }
