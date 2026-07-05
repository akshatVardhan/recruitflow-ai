from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.anyio
async def test_list_collections_endpoint():
    """The collections endpoint should return a dict with collection statuses."""
    # No Qdrant server is available in the test environment (unlike Postgres,
    # there's no Qdrant service container in CI), so mock the client the same
    # way test_retrieval.py's semantic search test already does.
    with patch("app.core.qdrant.get_qdrant_client") as mock_client:
        mock_qdrant = MagicMock()
        mock_qdrant.get_collection.side_effect = ValueError("not found")
        mock_client.return_value = mock_qdrant

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/rag/collections")
            assert response.status_code == 200
            data = response.json()
            assert "collections" in data
            assert "resumes" in data["collections"]
            assert "job_descriptions" in data["collections"]
            assert "hr_documents" in data["collections"]
