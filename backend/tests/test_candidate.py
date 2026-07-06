import pytest


@pytest.mark.anyio
async def test_list_candidates_requires_auth(client):
    response = await client.get("/api/v1/candidates/")
    assert response.status_code in (401, 403)


@pytest.mark.anyio
async def test_list_candidates_with_valid_token(client, auth_headers):
    response = await client.get("/api/v1/candidates/", headers=auth_headers)
    assert response.status_code == 200
