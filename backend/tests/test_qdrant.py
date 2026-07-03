import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.anyio
async def test_list_collections_endpoint():
    """The collections endpoint should return a dict with collection statuses."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/rag/collections")
        assert response.status_code == 200
        data = response.json()
        assert "collections" in data
        assert "resumes" in data["collections"]
        assert "job_descriptions" in data["collections"]
        assert "hr_documents" in data["collections"]
