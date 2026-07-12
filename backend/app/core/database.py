from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


def create_worker_session_factory() -> tuple[AsyncEngine, async_sessionmaker]:
    """Build an engine + session factory scoped to the caller's event loop.

    RF-89: asyncpg connections are bound to the event loop that created them.
    The module-level `engine`/`async_session_factory` above are fine for
    get_db() because FastAPI runs everything in one long-lived loop, but a
    Celery task that wraps its work in a fresh `asyncio.run()` per invocation
    gets a new loop each time - reusing the shared engine's pool there
    corrupts asyncpg's connection state on the second call in the same
    worker process. Call this once per event loop instead, and dispose the
    returned engine before that loop ends.
    """
    worker_engine = create_async_engine(settings.database_url, echo=False)
    worker_session_factory = async_sessionmaker(
        worker_engine, class_=AsyncSession, expire_on_commit=False
    )
    return worker_engine, worker_session_factory
