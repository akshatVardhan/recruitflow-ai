import io
import logging
import uuid

import fitz  # PyMuPDF
from docx import Document as DocxDocument
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.storage import download_file
from app.modules.documents.models import Document

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file using PyMuPDF."""
    text_parts: list[str] = []
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    for page_num in range(doc.page_count):
        page = doc[page_num]
        page_text = page.get_text()
        if page_text.strip():
            text_parts.append(page_text)
    doc.close()
    return "\n".join(text_parts).strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX file using python-docx."""
    text_parts: list[str] = []
    doc = DocxDocument(io.BytesIO(file_bytes))
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            text_parts.append(paragraph.text)
    return "\n".join(text_parts).strip()


async def extract_document_text(document_id: uuid.UUID, db: AsyncSession) -> str | None:
    """Download a document's file, extract text, update DB, and return the text."""
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.deleted_at.is_(None))
    )
    document = result.scalar_one_or_none()
    if document is None:
        logger.warning(f"Document {document_id} not found for extraction")
        return None

    try:
        file_bytes = await download_file(
            bucket=settings.doc_upload_bucket,
            key=document.file_path,
        )
    except Exception as e:
        logger.error(f"Failed to download file for document {document_id}: {e}")
        return None

    mime = document.mime_type or ""
    try:
        if "pdf" in mime or document.file_name.lower().endswith(".pdf"):
            extracted = extract_text_from_pdf(file_bytes)
        elif "word" in mime or document.file_name.lower().endswith(".docx"):
            extracted = extract_text_from_docx(file_bytes)
        else:
            logger.warning(f"Unsupported mime type '{mime}' for document {document_id}")
            return None
    except Exception as e:
        logger.error(f"Failed to parse file for document {document_id}: {e}")
        return None

    document.extracted_text = extracted
    await db.commit()
    await db.refresh(document)
    logger.info(f"Extracted {len(extracted)} chars from document {document_id}")
    return extracted
