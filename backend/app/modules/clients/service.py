import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.clients.models import Client
from app.modules.clients.schemas import ClientCreate


async def create_client(
    db: AsyncSession, user_id: uuid.UUID, data: ClientCreate
) -> Client:
    client = Client(user_id=user_id, name=data.name, industry=data.industry)
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client


async def list_clients(db: AsyncSession, user_id: uuid.UUID) -> list[Client]:
    result = await db.execute(
        select(Client)
        .where(Client.user_id == user_id, Client.deleted_at.is_(None))
        .order_by(Client.created_at)
    )
    return list(result.scalars().all())


async def get_client_for_user(
    db: AsyncSession, client_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[Client]:
    """Fetch a client scoped to its owner - None if it doesn't exist or
    belongs to someone else (see RF-78: callers should 404 either way)."""
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.user_id == user_id,
            Client.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()
