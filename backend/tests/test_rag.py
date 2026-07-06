import pytest


@pytest.mark.anyio
async def test_list_collections_requires_auth(client):
    response = await client.get("/api/v1/rag/collections")
    assert response.status_code in (401, 403)


@pytest.mark.anyio
async def test_list_collections_with_valid_token(client, auth_headers):
    """Requires a live Qdrant; validates auth passes at minimum."""
    response = await client.get("/api/v1/rag/collections", headers=auth_headers)
    assert response.status_code in (200, 500)


@pytest.mark.anyio
async def test_search_documents_requires_auth(client):
    response = await client.post(
        "/api/v1/rag/search",
        json={"query": "python developer", "client_id": "some-client"},
    )
    assert response.status_code in (401, 403)
