"""Shared document ingestion pipeline.

RF-92: extracted out of the Celery-specific worker.py so both the Cloud Run
Job entrypoint (app/ingest_once.py) and ingestion_trigger.py's local-dev
fallback can call it without depending on Celery.
"""

import logging

from sqlalchemy import select

# RF-89: whatever process calls run_ingestion_pipeline() first (Celery's
# worker.py previously, app/ingest_once.py now) must import these for their
# side effect of populating SQLAlchemy's declarative registry before the
# first query compiles a FK against them - app.main's router imports do
# this for FastAPI, but neither the old Celery entrypoint nor the new Job
# entrypoint import app.main. Do not remove as unused.
from app.modules.auth import models as _auth_models  # noqa: F401
from app.modules.clients import models as _client_models  # noqa: F401
from app.modules.documents import models as _document_models  # noqa: F401

logger = logging.getLogger(__name__)


async def run_ingestion_pipeline(document_id: str):
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
