"""Celery worker configuration and ingestion tasks."""

import asyncio
import logging
import ssl

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
    # Required whenever redis_url uses rediss:// (Upstash and most managed
    # Redis do) - Celery's redis result backend raises at task-send time
    # without this, even though the broker connection alone works fine.
    # No-op for plain redis:// (e.g. local fallback), safe to always set.
    broker_use_ssl={"ssl_cert_reqs": ssl.CERT_REQUIRED},
    redis_backend_use_ssl={"ssl_cert_reqs": ssl.CERT_REQUIRED},
)


@celery_app.task(
    bind=True, name="ingest_document", max_retries=3, default_retry_delay=60
)
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
    from app.modules.documents.models import Document, DocChunk

    async with async_session_factory() as db:
        result = await db.execute(
            select(Document).where(
                Document.id == document_id, Document.deleted_at.is_(None)
            )
        )
        doc = result.scalar_one_or_none()
        if doc is None:
            logger.error(f"Document {document_id} not found for ingestion")
            return

        try:
            # 1. Extract text
            doc.status = "extracting"
            await db.commit()
            text = await extract_document_text(doc.id, db)
            if not text:
                logger.error(f"Extraction failed for document {document_id}")
                doc.status = "failed"
                await db.commit()
                return

            await db.refresh(doc)

            # 2. Auto-tag
            tags = await auto_tag_document_text(doc.extracted_text or "")
            doc.auto_tags = tags

            # 3. Chunk
            doc.status = "chunking"
            await db.commit()
            chunks = chunk_document(doc)
            if not chunks:
                logger.warning(f"No chunks generated for document {document_id}")
                doc.status = "failed"
                await db.commit()
                return

            client_id = str(doc.client_id)
            doc_type = doc.doc_type

            # 4. Embed and store in Qdrant
            doc.status = "embedding"
            await db.commit()
            point_ids = await embed_and_store_chunks(chunks, doc_type, client_id, tags)

            # 5. Persist chunks + their Qdrant point IDs so they're queryable
            # and so a later delete/re-ingest can find the points to remove.
            db.add_all(
                DocChunk(
                    document_id=doc.id,
                    chunk_index=chunk["chunk_index"],
                    chunk_text=chunk["chunk_text"],
                    qdrant_point_id=point_id,
                )
                for chunk, point_id in zip(chunks, point_ids)
            )
            doc.status = "completed"
            await db.commit()

            logger.info(
                f"Stored {len(point_ids)} Qdrant points for document {document_id}"
            )
        except Exception:
            doc.status = "failed"
            await db.commit()
            raise
