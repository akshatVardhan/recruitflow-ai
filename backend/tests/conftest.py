import asyncio

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import Base, engine, async_session_factory


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


async def _reset_tables(create: bool) -> None:
    # dispose before/after so no pooled connection outlives the throwaway
    # loop that asyncio.run() creates for this fixture (see setup_database).
    await engine.dispose()
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all if create else Base.metadata.drop_all
        )
    await engine.dispose()


@pytest.fixture(autouse=True)
def setup_database():
    # Plain (sync) fixture: pytest 9 removed support for sync tests depending
    # on an async autouse fixture, so the async setup/teardown is driven via
    # asyncio.run() instead of `async def` + yield.
    asyncio.run(_reset_tables(create=True))
    yield
    asyncio.run(_reset_tables(create=False))


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session():
    async with async_session_factory() as session:
        yield session
