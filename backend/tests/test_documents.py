import uuid

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.anyio
async def test_upload_document_requires_file():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/documents/upload",
            data={
                "client_id": str(uuid.uuid4()),
                "title": "Test Document",
                "doc_type": "resume",
            },
        )
        # Expect 422 because file is required
        assert response.status_code == 422


@pytest.mark.anyio
async def test_get_nonexistent_document_returns_404():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/documents/{uuid.uuid4()}")
        assert response.status_code == 404


@pytest.mark.anyio
async def test_get_nonexistent_document_status_returns_404():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/documents/{uuid.uuid4()}/status")
        assert response.status_code == 404
