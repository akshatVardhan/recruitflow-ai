"""Tests for hybrid retrieval."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.rag.retriever import hybrid_search, semantic_search
from app.modules.rag.router import SearchRequest


def test_search_request_model():
    req = SearchRequest(query="python developer", client_id=str(uuid.uuid4()))
    assert req.query == "python developer"
    assert req.limit == 10


def test_semantic_search_empty_results():
    """Semantic search with no matching docs should return empty list."""
    with patch("app.modules.rag.retriever.embed_text", return_value=[0.1] * 384):
        with patch("app.modules.rag.retriever.get_qdrant_client") as mock_client:
            mock_qdrant = MagicMock()
            mock_qdrant.search.return_value = []
            mock_client.return_value = mock_qdrant

            results = semantic_search("test query", "client-1")
            assert results == []


@pytest.mark.anyio
async def test_hybrid_search_empty():
    """Hybrid search with no data should return empty results."""
    mock_db = AsyncMock()
    mock_db.execute.return_value.all.return_value = []

    with patch("app.modules.rag.retriever.semantic_search", return_value=[]):
        result = await hybrid_search(mock_db, "python", "client-1")
        assert result["total"] == 0
        assert result["results"] == []
