"""Tests for Celery worker and ingestion pipeline."""

import ssl
import uuid
from unittest.mock import patch, AsyncMock

import pytest

from app.worker import ingest_document, celery_app, _run_ingestion_pipeline
from app.modules.auth.models import User
from app.modules.clients.models import Client
from app.modules.documents.chunker import chunk_document
from app.modules.documents.models import Document
from app.modules.documents.service import get_document_chunks


def test_celery_app_config():
    """Celery app should be configured with Redis broker."""
    assert celery_app.conf.broker_url is not None
    assert celery_app.conf.task_serializer == "json"


def test_celery_app_configures_redis_ssl():
    """rediss:// backends (Upstash, most managed Redis) need ssl_cert_reqs set
    explicitly or the result backend raises ValueError at task-send time."""
    assert celery_app.conf.broker_use_ssl == {"ssl_cert_reqs": ssl.CERT_REQUIRED}
    assert celery_app.conf.redis_backend_use_ssl == {"ssl_cert_reqs": ssl.CERT_REQUIRED}


def test_ingest_task_registered():
    """ingest_document should be registered as a Celery task."""
    assert "ingest_document" in celery_app.tasks


@patch("app.worker._run_ingestion_pipeline")
def test_ingest_document_calls_pipeline(mock_pipeline):
    """ingest_document task should call the async pipeline."""
    result = ingest_document("test-doc-id")
    assert result["status"] == "completed"
    assert result["document_id"] == "test-doc-id"


async def _create_test_document(db_session, **overrides) -> Document:
    user = User(
        email=f"{uuid.uuid4()}@example.com",
        full_name="Test User",
        hashed_password="x",
    )
    db_session.add(user)
    await db_session.flush()

    client_row = Client(user_id=user.id, name="Test Client")
    db_session.add(client_row)
    await db_session.flush()

    fields = dict(
        title="Policy",
        doc_type="policy",
        file_path="documents/x/x.pdf",
        file_name="policy.pdf",
    )
    fields.update(overrides)
    doc = Document(client_id=client_row.id, user_id=user.id, **fields)
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)
    return doc


@pytest.mark.anyio
async def test_pipeline_persists_doc_chunks_with_qdrant_point_ids(db_session):
    """RF-57: after ingestion, each chunk must be persisted as a DocChunk row
    carrying the exact Qdrant point ID embed_and_store_chunks returned for it,
    so RF-58's delete/re-ingest flow can find the points to remove."""
    doc = await _create_test_document(
        db_session,
        extracted_text="Paragraph one.\n\n" + ("filler " * 600) + "\n\nParagraph two.",
    )

    # Real chunker output drives the fake point IDs, so this doesn't hardcode
    # a chunk count that paragraph-merging logic could silently invalidate.
    expected_chunks = chunk_document(doc)
    assert len(expected_chunks) > 1
    fake_point_ids = [uuid.uuid4() for _ in expected_chunks]

    with (
        patch(
            "app.modules.documents.extractor.extract_document_text",
            new=AsyncMock(return_value=doc.extracted_text),
        ),
        patch(
            "app.modules.documents.auto_tagger.auto_tag_document_text",
            new=AsyncMock(return_value={}),
        ),
        patch(
            "app.core.embeddings.embed_and_store_chunks",
            new=AsyncMock(return_value=fake_point_ids),
        ),
    ):
        await _run_ingestion_pipeline(str(doc.id))

    persisted = await get_document_chunks(db_session, doc.id)
    assert [c.qdrant_point_id for c in persisted] == fake_point_ids
    assert [c.chunk_index for c in persisted] == [
        c["chunk_index"] for c in expected_chunks
    ]
    assert [c.chunk_text for c in persisted] == [
        c["chunk_text"] for c in expected_chunks
    ]

    await db_session.refresh(doc)
    assert doc.status == "completed"


@pytest.mark.anyio
async def test_pipeline_marks_document_failed_on_extraction_failure(db_session):
    """RF-58: a failed extraction step must leave the document status as
    'failed', not silently stuck wherever it last was."""
    doc = await _create_test_document(db_session)
    assert doc.status == "uploaded"

    with patch(
        "app.modules.documents.extractor.extract_document_text",
        new=AsyncMock(return_value=None),
    ):
        await _run_ingestion_pipeline(str(doc.id))

    await db_session.refresh(doc)
    assert doc.status == "failed"


@pytest.mark.anyio
async def test_pipeline_marks_document_failed_on_unexpected_exception(db_session):
    """RF-58: an exception anywhere in the pipeline (e.g. the embedding call
    blowing up) must still land the document in 'failed', and propagate so
    Celery's retry logic still sees it."""
    doc = await _create_test_document(db_session, extracted_text="Some text.")

    with (
        patch(
            "app.modules.documents.extractor.extract_document_text",
            new=AsyncMock(return_value=doc.extracted_text),
        ),
        patch(
            "app.modules.documents.auto_tagger.auto_tag_document_text",
            new=AsyncMock(return_value={}),
        ),
        patch(
            "app.core.embeddings.embed_and_store_chunks",
            new=AsyncMock(side_effect=RuntimeError("qdrant is down")),
        ),
        pytest.raises(RuntimeError),
    ):
        await _run_ingestion_pipeline(str(doc.id))

    await db_session.refresh(doc)
    assert doc.status == "failed"
