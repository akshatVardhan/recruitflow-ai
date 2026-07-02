"""Celery worker configuration and ingestion tasks."""

import asyncio
import logging

from celery import Celery
from sqlalchemy import select

from app.core.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "recruitflow",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@celery_app.task(bind=True, name="ingest_document", max_retries=3, default_retry_delay=60)
def ingest_document(self, document_id: str):
    """Celery task: run full ingestion pipeline for a document.

    Orchestrates: extract -> auto-tag -> chunk -> embed.
    Runs inside an async event loop since all pipeline steps are async.
    """
    try:
        asyncio.run(_run_ingestion_pipeline(document_id))
        logger.info(f"Ingestion complete for document {document_id}")
        return {"status": "completed", "document_id": document_id}
    except Exception as e:
        logger.error(f"Ingestion failed for document {document_id}: {e}")
        self.retry(exc=e)


async def _run_ingestion_pipeline(document_id: str):
    """Async pipeline: extract -> tag -> chunk -> embed."""
    from app.core.database import async_session_factory
    from app.core.embeddings import embed_and_store_chunks
    from app.modules.documents.auto_tagger import auto_tag_document_text
    from app.modules.documents.chunker import chunk_document
    from app.modules.documents.extractor import extract_document_text
    from app.modules.documents.models import Document

    async with async_session_factory() as db:
        result = await db.execute(
            select(Document).where(Document.id == document_id, Document.deleted_at.is_(None))
        )
        doc = result.scalar_one_or_none()
        if doc is None:
            logger.error(f"Document {document_id} not found for ingestion")
            return

        # 1. Extract text
        text = await extract_document_text(doc.id, db)
        if not text:
            logger.error(f"Extraction failed for document {document_id}")
            return

        await db.refresh(doc)

        # 2. Auto-tag
        tags = await auto_tag_document_text(doc.extracted_text or "")
        doc.auto_tags = tags
        await db.commit()

        # 3. Chunk
        chunks = chunk_document(doc)
        if not chunks:
            logger.warning(f"No chunks generated for document {document_id}")
            return

        client_id = str(doc.client_id)
        doc_type = doc.doc_type

        # 4. Embed and store in Qdrant
        point_ids = await embed_and_store_chunks(chunks, doc_type, client_id, tags)

        logger.info(f"Stored {len(point_ids)} Qdrant points for document {document_id}")
