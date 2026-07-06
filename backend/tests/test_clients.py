import uuid

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.anyio
async def test_create_client_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/clients", json={"name": "Acme Staffing"})
        assert response.status_code in (401, 403)


@pytest.mark.anyio
async def test_list_clients_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/clients")
        assert response.status_code in (401, 403)


@pytest.mark.anyio
async def test_create_and_list_clients(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create = await client.post(
            "/api/v1/clients",
            json={"name": "Acme Staffing", "industry": "Recruiting"},
            headers=auth_headers,
        )
        assert create.status_code == 201
        body = create.json()
        assert body["name"] == "Acme Staffing"
        assert body["industry"] == "Recruiting"
        assert body["is_active"] is True

        listing = await client.get("/api/v1/clients", headers=auth_headers)
        assert listing.status_code == 200
        names = [c["name"] for c in listing.json()]
        assert "Acme Staffing" in names


@pytest.mark.anyio
async def test_client_industry_is_optional(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/clients", json={"name": "No Industry Client"}, headers=auth_headers
        )
        assert response.status_code == 201
        assert response.json()["industry"] is None


async def _register_and_login(client: AsyncClient, email: str) -> dict:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test", "password": "testpass123"},
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "testpass123"}
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.mark.anyio
async def test_clients_are_scoped_per_user():
    """A second user should not see the first user's clients."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers_a = await _register_and_login(client, f"{uuid.uuid4()}@example.com")
        headers_b = await _register_and_login(client, f"{uuid.uuid4()}@example.com")

        await client.post(
            "/api/v1/clients", json={"name": "User A's Client"}, headers=headers_a
        )
        listing_b = await client.get("/api/v1/clients", headers=headers_b)
        assert listing_b.json() == []
