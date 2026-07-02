"""Tests for document chunking strategies."""

import uuid
from unittest.mock import MagicMock

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.modules.documents.chunker import chunk_resume, chunk_job_description, chunk_document


SAMPLE_RESUME = """
Education
Bachelor of Science in Computer Science
University of Technology, 2020-2024

Experience
Software Engineer at TechCorp
Developed microservices using FastAPI and PostgreSQL

Skills
Python, FastAPI, PostgreSQL, Docker, AWS
"""

SAMPLE_JD = """
Role
Senior Backend Engineer

Requirements
5+ years Python experience, FastAPI, PostgreSQL

Responsibilities
Design and implement REST APIs, mentor junior engineers
"""

SAMPLE_POLICY = """
This is a company policy document.
All employees must adhere to the code of conduct.
Any violation should be reported to HR.
The policy is effective from January 1st 2026.
"""


def test_chunk_resume_by_section():
    doc_id = uuid.uuid4()
    chunks = chunk_resume(SAMPLE_RESUME, doc_id)
    assert len(chunks) >= 1
    assert all(c["document_id"] == doc_id for c in chunks)
    assert all("chunk_index" in c for c in chunks)


def test_chunk_jd_by_section():
    doc_id = uuid.uuid4()
    chunks = chunk_job_description(SAMPLE_JD, doc_id)
    assert len(chunks) >= 1
    assert all(c["document_id"] == doc_id for c in chunks)


def test_chunk_other_doc_type():
    doc_id = uuid.uuid4()
    mock_doc = MagicMock()
    mock_doc.id = doc_id
    mock_doc.extracted_text = SAMPLE_POLICY
    mock_doc.doc_type = "policy"
    chunks = chunk_document(mock_doc)
    assert len(chunks) >= 1


def test_chunk_empty_text():
    mock_doc = MagicMock()
    mock_doc.id = uuid.uuid4()
    mock_doc.extracted_text = ""
    mock_doc.doc_type = "resume"
    chunks = chunk_document(mock_doc)
    assert chunks == []


@pytest.mark.anyio
async def test_chunk_nonexistent_document_returns_404():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/api/v1/documents/{uuid.uuid4()}/chunk")
        assert response.status_code == 404
