import asyncio
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import engine, async_session_factory

# Real migrations, not Base.metadata.create_all(): Client ORM model is still
# an empty stub (User now exists, see auth/models.py), so Document's FK to
# clients can't be resolved from Base.metadata alone. The migrations already
# define that table for real.
ALEMBIC_CFG = Config(str(Path(__file__).resolve().parent.parent / "alembic.ini"))


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def setup_database():
    # Plain (sync) fixture: pytest 9 removed support for sync tests depending
    # on an async autouse fixture. alembic's command.upgrade/downgrade are sync
    # APIs (they drive their own asyncio.run() internally via env.py), so no
    # asyncio.run() wrapper is needed here for the schema step itself.
    # Dispose the app's engine around each test so no pooled connection from
    # one test's event loop is reused by the next test's (different) loop.
    asyncio.run(engine.dispose())
    command.upgrade(ALEMBIC_CFG, "head")
    yield
    command.downgrade(ALEMBIC_CFG, "base")
    asyncio.run(engine.dispose())


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session():
    async with async_session_factory() as session:
        yield session


@pytest.fixture
async def auth_headers(client):
    """Register + log in a throwaway user, return a bearer auth header."""
    email = f"{uuid.uuid4()}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test User", "password": "testpass123"},
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "testpass123"}
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _make_tenant(client: AsyncClient) -> dict:
    """Register + log in a throwaway user, create a client they own.

    Returns {"headers": ..., "client_id": ...} - everything a test needs to
    act as this tenant and prove another tenant can't reach their data.
    """
    email = f"{uuid.uuid4()}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test User", "password": "testpass123"},
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "testpass123"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    create = await client.post(
        "/api/v1/clients", json={"name": "Test Client"}, headers=headers
    )
    return {"headers": headers, "client_id": create.json()["id"]}


@pytest.fixture
async def tenant_a(client):
    """RF-66: one of two distinct users, each with their own client."""
    return await _make_tenant(client)


@pytest.fixture
async def tenant_b(client):
    """RF-66: the other of two distinct users, each with their own client."""
    return await _make_tenant(client)
