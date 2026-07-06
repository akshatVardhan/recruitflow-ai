import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ClientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    industry: str | None = Field(default=None, max_length=200)


class ClientResponse(BaseModel):
    id: uuid.UUID
    name: str
    industry: str | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
