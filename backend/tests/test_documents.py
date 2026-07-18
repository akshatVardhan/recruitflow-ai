import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.modules.clients.models import Client
from app.modules.documents import router as documents_router
from app.modules.documents.models import Document, DocChunk
from app.modules.documents.service import get_document_chunks


async def _auth_headers(client: AsyncClient) -> dict:
    """Register + log in a throwaway user, return a bearer auth header."""
    email = f"{uuid.uuid4()}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test User", "password": "testpass123"},
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "testpass123"}
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _owned_client_id(client: AsyncClient, headers: dict) -> str:
    """Create a real client owned by whoever `headers` authenticates as."""
    response = await client.post(
        "/api/v1/clients", json={"name": "Test Client"}, headers=headers
    )
    return response.json()["id"]


@pytest.mark.anyio
async def test_upload_document_requires_auth():
    """POST /upload without a bearer token should be rejected, not reach validation."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/documents/upload",
            data={
                "client_id": str(uuid.uuid4()),
                "title": "Test Document",
                "doc_type": "resume",
            },
        )
        assert response.status_code in (401, 403)


@pytest.mark.anyio
async def test_upload_document_requires_file():
    """POST /upload without file should return 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _auth_headers(client)
        response = await client.post(
            "/api/v1/documents/upload",
            data={
                "client_id": str(uuid.uuid4()),
                "title": "Test Document",
                "doc_type": "resume",
            },
            headers=headers,
        )
        assert response.status_code == 422


@pytest.mark.anyio
async def test_upload_document_invalid_doc_type():
    """POST /upload with invalid doc_type should return 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _auth_headers(client)
        response = await client.post(
            "/api/v1/documents/upload",
            data={
                "client_id": str(uuid.uuid4()),
                "title": "Test",
                "doc_type": "invalid_doc_type_xyz",
            },
            headers=headers,
        )
        assert response.status_code == 422


@pytest.mark.anyio
async def test_upload_document_success():
    """POST /upload with valid data, a real token, and an owned client should return 201."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _auth_headers(client)
        client_id = await _owned_client_id(client, headers)
        with (
            patch(
                "app.modules.documents.router.trigger_ingestion",
                new_callable=AsyncMock,
            ) as mock_trigger,
            patch(
                "app.modules.documents.service.upload_file",
                new_callable=AsyncMock,
            ),
        ):
            response = await client.post(
                "/api/v1/documents/upload",
                data={
                    "client_id": client_id,
                    "title": "Test Resume",
                    "doc_type": "resume",
                },
                files={
                    "file": ("test.pdf", b"%PDF-1.4 mock content", "application/pdf")
                },
                headers=headers,
            )
        assert response.status_code == 201
        mock_trigger.assert_awaited_once_with(response.json()["id"])


@pytest.mark.anyio
async def test_upload_document_rejects_oversized_file(monkeypatch):
    """RF-59: files over the size cap must be rejected with 413, before upload/DB work."""
    monkeypatch.setattr(documents_router, "MAX_FILE_SIZE_BYTES", 10)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _auth_headers(client)
        client_id = await _owned_client_id(client, headers)
        response = await client.post(
            "/api/v1/documents/upload",
            data={"client_id": client_id, "title": "Big File", "doc_type": "resume"},
            files={"file": ("big.pdf", b"way more than ten bytes", "application/pdf")},
            headers=headers,
        )
        assert response.status_code == 413


@pytest.mark.anyio
async def test_upload_document_rejects_disallowed_extension():
    """RF-59: only .pdf/.docx files are accepted; anything else is 415."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _auth_headers(client)
        client_id = await _owned_client_id(client, headers)
        response = await client.post(
            "/api/v1/documents/upload",
            data={"client_id": client_id, "title": "Script", "doc_type": "resume"},
            files={
                "file": ("payload.exe", b"MZ mock binary", "application/octet-stream")
            },
            headers=headers,
        )
        assert response.status_code == 415


@pytest.mark.anyio
async def test_upload_document_rejects_mismatched_mime_type():
    """RF-59: a .pdf-named file whose declared content-type isn't PDF/DOCX must 415 too."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _auth_headers(client)
        client_id = await _owned_client_id(client, headers)
        response = await client.post(
            "/api/v1/documents/upload",
            data={"client_id": client_id, "title": "Spoofed", "doc_type": "resume"},
            files={"file": ("resume.pdf", b"not really a pdf", "text/plain")},
            headers=headers,
        )
        assert response.status_code == 415


@pytest.mark.anyio
async def test_upload_document_rejects_fake_pdf_with_correct_extension_and_mime():
    """RF-59 follow-up: extension and Content-Type are both client-supplied
    and can be spoofed together (rename a file, send a matching fake
    header) - magic-byte sniffing on the real content must still catch it."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _auth_headers(client)
        client_id = await _owned_client_id(client, headers)
        response = await client.post(
            "/api/v1/documents/upload",
            data={"client_id": client_id, "title": "Fake PDF", "doc_type": "resume"},
            files={
                "file": ("resume.pdf", b"just plain text, not a pdf", "application/pdf")
            },
            headers=headers,
        )
        assert response.status_code == 415


@pytest.mark.anyio
async def test_upload_document_rejects_unowned_client():
    """POST /upload with a client_id belonging to a different user should 404, not 201."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        owner_headers = await _auth_headers(client)
        other_client_id = await _owned_client_id(client, owner_headers)

        attacker_headers = await _auth_headers(client)
        response = await client.post(
            "/api/v1/documents/upload",
            data={
                "client_id": other_client_id,
                "title": "Test Resume",
                "doc_type": "resume",
            },
            files={"file": ("test.pdf", b"%PDF-1.4 mock content", "application/pdf")},
            headers=attacker_headers,
        )
        assert response.status_code == 404


@pytest.mark.anyio
async def test_get_nonexistent_document_returns_404():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _auth_headers(client)
        response = await client.get(
            f"/api/v1/documents/{uuid.uuid4()}", headers=headers
        )
        assert response.status_code == 404


@pytest.mark.anyio
async def test_get_nonexistent_document_status_returns_404():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _auth_headers(client)
        response = await client.get(
            f"/api/v1/documents/{uuid.uuid4()}/status", headers=headers
        )
        assert response.status_code == 404


@pytest.mark.anyio
@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/api/v1/documents/{id}"),
        ("GET", "/api/v1/documents/{id}/status"),
        ("POST", "/api/v1/documents/{id}/chunk"),
        ("POST", "/api/v1/documents/{id}/extract"),
        ("POST", "/api/v1/documents/{id}/tag"),
        ("POST", "/api/v1/documents/{id}/reingest"),
    ],
)
async def test_document_endpoints_require_auth(method, path):
    """RF-78: every non-upload documents endpoint must reject anonymous requests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        url = path.format(id=uuid.uuid4())
        response = await client.request(method, url)
        assert response.status_code in (401, 403)


@pytest.mark.anyio
async def test_get_document_rejects_other_users_document():
    """RF-78: an authenticated user must not be able to read another user's document by ID."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        owner_headers = await _auth_headers(client)
        client_id = await _owned_client_id(client, owner_headers)
        upload = await client.post(
            "/api/v1/documents/upload",
            data={"client_id": client_id, "title": "Secret", "doc_type": "resume"},
            files={"file": ("test.pdf", b"%PDF-1.4 mock content", "application/pdf")},
            headers=owner_headers,
        )
        if upload.status_code != 201:
            pytest.skip(
                "upload did not succeed in this environment (DB/MinIO), nothing to check ownership against"
            )
        document_id = upload.json()["id"]

        attacker_headers = await _auth_headers(client)
        response = await client.get(
            f"/api/v1/documents/{document_id}", headers=attacker_headers
        )
        assert response.status_code == 404


@pytest.mark.anyio
async def test_reingest_deletes_stale_chunks_and_vectors_before_requeue(db_session):
    """RF-58: reingest must remove a document's existing DocChunk rows and
    their Qdrant points before re-queuing ingestion - otherwise an update
    leaves stale vectors sitting alongside the freshly re-ingested ones."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = await _auth_headers(client)
        me = await client.get("/api/v1/auth/me", headers=headers)
        user_id = uuid.UUID(me.json()["id"])

        client_row = Client(user_id=user_id, name="Test Client")
        db_session.add(client_row)
        await db_session.flush()

        doc = Document(
            client_id=client_row.id,
            user_id=user_id,
            title="Resume",
            doc_type="resume",
            file_path="documents/x/x.pdf",
            file_name="resume.pdf",
            status="completed",
        )
        db_session.add(doc)
        await db_session.flush()

        stale_point_ids = [uuid.uuid4(), uuid.uuid4()]
        db_session.add_all(
            DocChunk(
                document_id=doc.id,
                chunk_index=i,
                chunk_text=f"chunk {i}",
                qdrant_point_id=point_id,
            )
            for i, point_id in enumerate(stale_point_ids)
        )
        await db_session.commit()

        mock_qdrant = MagicMock()
        with (
            patch(
                "app.modules.documents.service.get_qdrant_client",
                return_value=mock_qdrant,
            ),
            patch(
                "app.modules.documents.router.trigger_ingestion",
                new_callable=AsyncMock,
            ) as mock_trigger,
        ):
            response = await client.post(
                f"/api/v1/documents/{doc.id}/reingest", headers=headers
            )

        assert response.status_code == 200
        mock_trigger.assert_awaited_once_with(str(doc.id))

        mock_qdrant.delete.assert_called_once()
        _, kwargs = mock_qdrant.delete.call_args
        assert kwargs["collection_name"] == "resumes"
        assert set(kwargs["points_selector"]) == {str(p) for p in stale_point_ids}

        remaining = await get_document_chunks(db_session, doc.id)
        assert remaining == []
