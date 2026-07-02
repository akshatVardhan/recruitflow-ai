"""Tests for embedding pipeline."""

from unittest.mock import MagicMock, patch

from app.core.embeddings import _get_qdrant_collection_name, _build_payload


def test_collection_mapping_resume():
    assert _get_qdrant_collection_name("resume") == "resumes"


def test_collection_mapping_jd():
    assert _get_qdrant_collection_name("job_description") == "job_descriptions"


def test_collection_mapping_other():
    assert _get_qdrant_collection_name("policy") == "hr_documents"


def test_build_payload_resume():
    chunk = {"document_id": "abc-123", "chunk_index": 0}
    payload = _build_payload(chunk, "resume", "client-1", {"candidate_name": "John", "skills": ["Python"]})
    assert payload["doc_id"] == "abc-123"
    assert payload["client_id"] == "client-1"
    assert payload["candidate_name"] == "John"
    assert "Python" in payload["skills"]


def test_build_payload_jd():
    chunk = {"document_id": "def-456", "chunk_index": 1}
    payload = _build_payload(chunk, "job_description", "client-2", {"role": "Engineer"})
    assert payload["job_title"] == "Engineer"
    assert payload["client_id"] == "client-2"


def test_build_payload_hr():
    chunk = {"document_id": "ghi-789", "chunk_index": 2}
    payload = _build_payload(chunk, "policy", "client-3", {"skills": ["compliance"]})
    assert payload["doc_type"] == "policy"
    assert "compliance" in payload["tags"]
