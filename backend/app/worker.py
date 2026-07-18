"""Celery worker configuration and ingestion tasks."""

import asyncio
import logging
import ssl

from celery import Celery
from sqlalchemy import select

from app.core.config import settings

# RF-89: `celery -A app.worker worker` imports only this module, never
# app.main - so unlike the FastAPI app (which pulls in every model via its
# router imports before the first request), nothing has registered these
# tables with SQLAlchemy's declarative Base before a task's first query
# tries to compile a FK against them. Import for the side effect of
# populating the shared registry; do not remove as unused.
from app.modules.auth import models as _auth_models  # noqa: F401
from app.modules.clients import models as _client_models  # noqa: F401
from app.modules.documents import models as _document_models  # noqa: F401

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
    # RF-89: with late acks and no visibility timeout, Redis redelivers an
    # unacked task fresh whenever the worker container restarts for reasons
    # unrelated to the task itself (e.g. Cloud Run cycling the instance) -
    # and each redelivery resets Celery's own per-task retry counter, so
    # max_retries=3 above never actually capped total attempts across
    # restarts. This bounds redelivery to genuinely stuck/crashed tasks
    # instead of ordinary restarts; it doesn't eliminate redelivery
    # entirely (inherent to at-least-once broker delivery). Set well above
    # a realistic worst-case ingestion run (large doc + embedding).
    broker_transport_options={"visibility_timeout": 3600},
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
        final_status = asyncio.run(_run_ingestion_pipeline(document_id))
        if final_status != "completed":
            # Not an exception - _run_ingestion_pipeline already persisted
            # doc.status="failed" itself (e.g. extraction yielded no text).
            # Report that here too, so this task's own return value/logs
            # don't claim "completed" for a document that's actually failed.
            logger.error(
                f"Ingestion did not complete for document {document_id}: "
                f"status={final_status}"
            )
            return {"status": final_status, "document_id": document_id}
        logger.info(f"Ingestion complete for document {document_id}")
        return {"status": "completed", "document_id": document_id}
    except Exception as e:
        logger.error(f"Ingestion failed for document {document_id}: {e}")
        self.retry(exc=e)


async def _run_ingestion_pipeline(document_id: str):
    """Async pipeline: extract -> tag -> chunk -> embed."""
    from app.core.database import create_worker_session_factory
    from app.core.embeddings import embed_and_store_chunks
    from app.modules.documents.auto_tagger import auto_tag_document_text
    from app.modules.documents.chunker import chunk_document
    from app.modules.documents.extractor import extract_document_text
    from app.modules.documents.models import Document, DocChunk

    # RF-89: this coroutine runs inside a fresh asyncio.run() per task
    # (see ingest_document below), so it gets a new event loop every call -
    # build a session factory scoped to that loop rather than reusing
    # database.py's module-level one (which get_db() keeps bound to
    # FastAPI's single long-lived loop), and dispose it before returning.
    worker_engine, session_factory = create_worker_session_factory()
    try:
        async with session_factory() as db:
            result = await db.execute(
                select(Document).where(
                    Document.id == document_id, Document.deleted_at.is_(None)
                )
            )
            doc = result.scalar_one_or_none()
            if doc is None:
                logger.error(f"Document {document_id} not found for ingestion")
                return "not_found"

            try:
                # 1. Extract text
                doc.status = "extracting"
                await db.commit()
                text = await extract_document_text(doc.id, db)
                if not text:
                    logger.error(f"Extraction failed for document {document_id}")
                    doc.status = "failed"
                    await db.commit()
                    return "failed"

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
                    return "failed"

                client_id = str(doc.client_id)
                doc_type = doc.doc_type

                # 4. Embed and store in Qdrant
                doc.status = "embedding"
                await db.commit()
                point_ids = await embed_and_store_chunks(
                    chunks, doc_type, client_id, tags
                )

                # 5. Persist chunks + their Qdrant point IDs so they're
                # queryable and so a later delete/re-ingest can find the
                # points to remove.
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
                return "completed"
            except Exception:
                doc.status = "failed"
                await db.commit()
                raise
    finally:
        await worker_engine.dispose()
