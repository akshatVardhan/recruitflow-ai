import uuid

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


def _unique_email() -> str:
    return f"{uuid.uuid4()}@example.com"


@pytest.mark.anyio
async def test_register_creates_user():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        email = _unique_email()
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "full_name": "Ada Lovelace",
                "password": "testpass123",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["email"] == email
        assert body["full_name"] == "Ada Lovelace"
        assert "password" not in body
        assert "hashed_password" not in body


@pytest.mark.anyio
async def test_register_duplicate_email_fails():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        email = _unique_email()
        payload = {"email": email, "full_name": "Ada", "password": "testpass123"}
        first = await client.post("/api/v1/auth/register", json=payload)
        assert first.status_code == 201
        second = await client.post("/api/v1/auth/register", json=payload)
        assert second.status_code == 400


@pytest.mark.anyio
async def test_login_success_returns_access_token_and_user_sets_refresh_cookie():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        email = _unique_email()
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "full_name": "Ada", "password": "testpass123"},
        )
        response = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": "testpass123"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["access_token"]
        assert body["token_type"] == "bearer"
        assert body["user"]["email"] == email
        # The refresh token must never appear in the JSON body - only as a
        # cookie the interceptor (frontend/lib/api.ts) already expects.
        assert "refresh_token" not in body
        assert client.cookies.get("refresh_token") is not None


@pytest.mark.anyio
async def test_login_wrong_password_fails():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        email = _unique_email()
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "full_name": "Ada", "password": "testpass123"},
        )
        response = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": "wrongpassword"}
        )
        assert response.status_code == 401


@pytest.mark.anyio
async def test_login_nonexistent_user_fails():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": _unique_email(), "password": "whatever123"},
        )
        assert response.status_code == 401


@pytest.mark.anyio
async def test_me_requires_token():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/auth/me")
        assert response.status_code in (401, 403)


@pytest.mark.anyio
async def test_me_with_valid_token_returns_user():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        email = _unique_email()
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "full_name": "Ada", "password": "testpass123"},
        )
        login = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": "testpass123"}
        )
        token = login.json()["access_token"]
        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["email"] == email


@pytest.mark.anyio
async def test_me_with_garbage_token_fails():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
        )
        assert response.status_code == 401


@pytest.mark.anyio
async def test_refresh_without_cookie_fails():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/auth/refresh")
        assert response.status_code == 401


@pytest.mark.anyio
async def test_refresh_issues_new_access_token():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        email = _unique_email()
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "full_name": "Ada", "password": "testpass123"},
        )
        # login sets the refresh cookie on this client's cookie jar; httpx
        # sends it back automatically on the next request to the same path.
        await client.post(
            "/api/v1/auth/login", json={"email": email, "password": "testpass123"}
        )
        response = await client.post("/api/v1/auth/refresh")
        assert response.status_code == 200
        assert response.json()["access_token"]
        # Rotation: a fresh refresh cookie is issued on every refresh.
        assert client.cookies.get("refresh_token") is not None


@pytest.mark.anyio
async def test_refresh_rejects_access_token_used_as_refresh_cookie():
    """An access token must not work if forced into the refresh cookie slot."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        email = _unique_email()
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "full_name": "Ada", "password": "testpass123"},
        )
        login = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": "testpass123"}
        )
        access_token = login.json()["access_token"]
        client.cookies.set("refresh_token", access_token)
        response = await client.post("/api/v1/auth/refresh")
        assert response.status_code == 401


@pytest.mark.anyio
async def test_refresh_rotation_invalidates_old_token():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        email = _unique_email()
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "full_name": "Ada", "password": "testpass123"},
        )
        await client.post(
            "/api/v1/auth/login", json={"email": email, "password": "testpass123"}
        )
        old_refresh_token = client.cookies.get("refresh_token")
        first = await client.post("/api/v1/auth/refresh")
        assert first.status_code == 200
        # Replay the pre-rotation cookie value directly: it was revoked
        # server-side the moment the new refresh token was issued.
        client.cookies.set("refresh_token", old_refresh_token)
        second = await client.post("/api/v1/auth/refresh")
        assert second.status_code == 401


@pytest.mark.anyio
async def test_logout_revokes_refresh_token_server_side():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        email = _unique_email()
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "full_name": "Ada", "password": "testpass123"},
        )
        await client.post(
            "/api/v1/auth/login", json={"email": email, "password": "testpass123"}
        )
        refresh_token = client.cookies.get("refresh_token")
        await client.post("/api/v1/auth/logout")
        # The cookie is cleared client-side; replay the raw value to confirm
        # logout also revoked it server-side, not just cleared the cookie.
        client.cookies.set("refresh_token", refresh_token)
        response = await client.post("/api/v1/auth/refresh")
        assert response.status_code == 401


@pytest.mark.anyio
async def test_logout_clears_refresh_cookie():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        email = _unique_email()
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "full_name": "Ada", "password": "testpass123"},
        )
        await client.post(
            "/api/v1/auth/login", json={"email": email, "password": "testpass123"}
        )
        assert client.cookies.get("refresh_token") is not None
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 200
        assert client.cookies.get("refresh_token") is None
