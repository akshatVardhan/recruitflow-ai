import uuid

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
        json={"query": "python developer", "client_id": str(uuid.uuid4())},
    )
    assert response.status_code in (401, 403)


@pytest.mark.anyio
async def test_search_rejects_unowned_client(client, tenant_a, tenant_b):
    """RF-68/RF-66: tenant B must not be able to run a RAG search scoped to
    tenant A's client_id - proves tenant isolation at the RAG boundary, the
    one endpoint that had zero ownership check before this fix."""
    response = await client.post(
        "/api/v1/rag/search",
        json={"query": "python developer", "client_id": tenant_a["client_id"]},
        headers=tenant_b["headers"],
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_search_accepts_owned_client(client, tenant_a):
    """A tenant searching their own client_id should pass the ownership
    check (may still 500 without a live Qdrant, but must not 404)."""
    response = await client.post(
        "/api/v1/rag/search",
        json={"query": "python developer", "client_id": tenant_a["client_id"]},
        headers=tenant_a["headers"],
    )
    assert response.status_code in (200, 500)
