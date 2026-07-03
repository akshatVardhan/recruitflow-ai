import uuid
from datetime import datetime
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DocType(StrEnum):
    resume = "resume"
    job_description = "job_description"
    offer_letter = "offer_letter"
    sop = "sop"
    performance_report = "performance_report"
    policy = "policy"
    contract = "contract"
    other = "other"


class DocumentUploadResponse(BaseModel):
    id: uuid.UUID
    title: str
    doc_type: str
    file_name: str
    file_size_kb: Optional[int] = None
    status: str = "uploaded"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentStatusResponse(BaseModel):
    id: uuid.UUID
    title: str
    doc_type: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    user_id: uuid.UUID
    title: str
    doc_type: str
    file_path: str
    file_name: str
    file_size_kb: Optional[int] = None
    mime_type: Optional[str] = None
    extracted_text: Optional[str] = None
    auto_tags: Optional[dict] = None
    manual_tags: Optional[list[str]] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
