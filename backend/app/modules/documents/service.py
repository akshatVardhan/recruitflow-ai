import logging
import uuid
from typing import Optional

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.storage import delete_file, upload_file
from app.modules.documents.models import Document

logger = logging.getLogger(__name__)


async def create_document(
    db: AsyncSession,
    client_id: uuid.UUID,
    user_id: uuid.UUID,
    title: str,
    doc_type: str,
    file: UploadFile,
) -> Document:
    file_bytes = await file.read()
    file_size_kb = len(file_bytes) // 1024

    doc_id = uuid.uuid4()
    file_ext = file.filename.rsplit(".", 1)[-1] if "." in (file.filename or "") else "bin"
    file_path = f"documents/{client_id}/{doc_id}.{file_ext}"

    # Upload blob to storage first
    await upload_file(
        bucket=settings.doc_upload_bucket,
        key=file_path,
        data=file_bytes,
        content_type=file.content_type or "application/octet-stream",
    )

    # If DB operation fails, clean up the blob
    try:
        document = Document(
            id=doc_id,
            client_id=client_id,
            user_id=user_id,
            title=title,
            doc_type=doc_type,
            file_path=file_path,
            file_name=file.filename or "untitled",
            file_size_kb=file_size_kb,
            mime_type=file.content_type,
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)
        return document
    except Exception as e:
        logger.error(f"DB commit failed after blob upload, cleaning up {file_path}: {e}")
        await delete_file(bucket=settings.doc_upload_bucket, key=file_path)
        raise


async def get_document(db: AsyncSession, document_id: uuid.UUID) -> Optional[Document]:
    result = await db.execute(select(Document).where(Document.id == document_id, Document.deleted_at.is_(None)))
    return result.scalar_one_or_none()


async def get_document_status(db: AsyncSession, document_id: uuid.UUID) -> Optional[dict]:
    doc = await get_document(db, document_id)
    if doc is None:
        return None
    return {
        "id": doc.id,
        "title": doc.title,
        "doc_type": doc.doc_type,
        "status": "uploaded",
        "created_at": doc.created_at,
    }
