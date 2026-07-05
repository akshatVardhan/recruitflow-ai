"""Tests for auto-tagging via GLM 5.2 (DeepInfra)."""

import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.modules.documents.auto_tagger import AutoTags, auto_tag_document_text


def test_auto_tags_model_defaults():
    """AutoTags model should have sensible defaults."""
    tags = AutoTags()
    assert tags.document_type == "other"
    assert tags.candidate_name is None
    assert tags.skills == []


def test_auto_tags_model_valid():
    """AutoTags model should accept valid data."""
    tags = AutoTags(
        document_type="resume",
        candidate_name="John Doe",
        role="Software Engineer",
        company="Acme Corp",
        skills=["Python", "FastAPI"],
        date="2026-01-15",
    )
    assert tags.document_type == "resume"
    assert tags.candidate_name == "John Doe"
    assert len(tags.skills) == 2


@pytest.mark.anyio
async def test_auto_tag_empty_text():
    """Empty text should return default tags."""
    result = await auto_tag_document_text("")
    assert result["document_type"] == "other"
    assert result["skills"] == []


@pytest.mark.anyio
async def test_auto_tag_with_mocked_llm():
    """Test parsing of mocked LiteLLM response."""
    mock_response = AsyncMock()
    mock_response.choices = [
        AsyncMock(
            message=AsyncMock(
                content=json.dumps(
                    {
                        "document_type": "resume",
                        "candidate_name": "Jane Smith",
                        "role": "Data Scientist",
                        "company": "TechCorp",
                        "skills": ["Python", "ML", "SQL"],
                        "date": "2026-03-10",
                    }
                )
            )
        )
    ]

    with patch(
        "app.modules.documents.auto_tagger.litellm.acompletion",
        return_value=mock_response,
    ):
        result = await auto_tag_document_text("Sample resume text here")
        assert result["document_type"] == "resume"
        assert result["candidate_name"] == "Jane Smith"
        assert "Python" in result["skills"]


@pytest.mark.anyio
async def test_tag_nonexistent_document_returns_404():
    """Tagging a nonexistent document should return 404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/api/v1/documents/{uuid.uuid4()}/tag")
        assert response.status_code == 404
