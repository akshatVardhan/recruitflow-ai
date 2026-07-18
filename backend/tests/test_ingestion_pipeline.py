"""Tests for the shared ingestion pipeline (RF-92: moved out of worker.py)."""

import uuid
from unittest.mock import patch, AsyncMock

import pytest

from app.core.ingestion_pipeline import run_ingestion_pipeline
from app.modules.auth.models import User
from app.modules.clients.models import Client
from app.modules.documents.chunker import chunk_document
from app.modules.documents.models import Document
from app.modules.documents.service import get_document_chunks


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
        await run_ingestion_pipeline(str(doc.id))

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
        await run_ingestion_pipeline(str(doc.id))

    await db_session.refresh(doc)
    assert doc.status == "failed"


@pytest.mark.anyio
async def test_pipeline_marks_document_failed_on_unexpected_exception(db_session):
    """RF-58: an exception anywhere in the pipeline (e.g. the embedding call
    blowing up) must still land the document in 'failed', and propagate so
    the caller's own retry logic (Cloud Run Job --max-retries as of RF-92)
    still sees it."""
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
        await run_ingestion_pipeline(str(doc.id))

    await db_session.refresh(doc)
    assert doc.status == "failed"
