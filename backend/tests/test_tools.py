"""Tests for RAG agent tools."""

import json
from unittest.mock import patch

import pytest

from app.modules.rag.tools import (
    ALL_TOOLS,
    search_documents_fn,
    get_document_by_id_fn,
)


def test_all_tools_registered():
    """All 5 tools should be registered."""
    assert len(ALL_TOOLS) == 5


def test_tool_names():
    """Tool names should match expected values."""
    names = [t.metadata.name for t in ALL_TOOLS]
    assert "search_documents" in names
    assert "get_document_by_id" in names
    assert "generate_document" in names
    assert "score_resume" in names
    assert "list_candidates" in names


@pytest.mark.anyio
async def test_get_document_by_id_not_found():
    """Getting a nonexistent document should return error JSON."""
    result = await get_document_by_id_fn(str(__import__("uuid").uuid4()))
    parsed = json.loads(result)
    assert "error" in parsed


@pytest.mark.anyio
async def test_search_documents_empty():
    """Searching with no data should return empty results."""
    with patch("app.modules.rag.tools.hybrid_search") as mock_search:
        mock_search.return_value = {
            "query": "test",
            "total": 0,
            "results": [],
            "sources": {"keyword_count": 0, "semantic_count": 0},
        }
        result = await search_documents_fn("test query", "client-1")
        parsed = json.loads(result)
        assert parsed["total"] == 0
