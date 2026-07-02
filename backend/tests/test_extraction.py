"""Tests for document text extraction."""

import uuid

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.modules.documents.extractor import extract_text_from_pdf, extract_text_from_docx


def test_extract_text_from_pdf_with_sample():
    """Test PDF extraction with a minimal valid PDF."""
    minimal_pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
        b"xref\n"
        b"0 4\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"trailer<</Size 4/Root 1 0 R>>\n"
        b"startxref\n"
        b"190\n"
        b"%%EOF"
    )
    text = extract_text_from_pdf(minimal_pdf)
    # A minimal PDF with no text content should return empty string
    assert isinstance(text, str)


def test_extract_text_from_docx_empty():
    """Test DOCX extraction returns a string even for empty doc."""
    import io
    import zipfile

    # Build a minimal valid DOCX (ZIP with required XML files)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("word/document.xml", "<?xml version=\"1.0\"?><w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"><w:body><w:p><w:r><w:t>Hello World</w:t></w:r></w:p></w:body></w:document>")
        zf.writestr("[Content_Types].xml", "<?xml version=\"1.0\"?><Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\"><Default Extension=\"xml\" ContentType=\"application/xml\"/><Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/><Override PartName=\"/word/document.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml\"/></Types>")
        zf.writestr("_rels/.rels", "<?xml version=\"1.0\"?><Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\"><Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"word/document.xml\"/></Relationships>")
        zf.writestr("word/_rels/document.xml.rels", "<?xml version=\"1.0\"?><Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\"></Relationships>")
    buf.seek(0)
    docx_bytes = buf.read()

    text = extract_text_from_docx(docx_bytes)
    assert isinstance(text, str)
    assert "Hello World" in text


@pytest.mark.anyio
async def test_extract_nonexistent_document_returns_404():
    """Extracting a nonexistent document should return 404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/api/v1/documents/{uuid.uuid4()}/extract")
        assert response.status_code == 404
