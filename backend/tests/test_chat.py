import pytest


@pytest.mark.anyio
async def test_chat_stream_requires_auth(client):
    response = await client.post("/api/v1/chat/stream")
    assert response.status_code in (401, 403)


@pytest.mark.anyio
async def test_chat_stream_with_valid_token(client, auth_headers):
    response = await client.post("/api/v1/chat/stream", headers=auth_headers)
    assert response.status_code == 200
