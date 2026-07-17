import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.models import User
from app.modules.auth.service import get_current_user
from app.modules.documents.auto_tagger import tag_document
from app.modules.documents.chunker import chunk_document
from app.modules.documents.extractor import extract_document_text
from app.modules.documents.schemas import (
    DocType,
    DocumentDetailResponse,
    DocumentStatusResponse,
    DocumentUploadResponse,
)
from app.modules.clients.service import get_client_for_user
from app.modules.documents.service import (
    create_document,
    delete_document_vectors_and_chunks,
    get_document_for_user,
    get_document_status,
)
from app.core.ingestion_trigger import trigger_ingestion

router = APIRouter()

# Matches the frontend's file-dropzone.tsx (MAX_FILE_SIZE / ACCEPTED_TYPES) -
# that 20 MB limit is the actual shipped/tested policy, not the 10 MB figure
# in stale planning docs.
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
# RF-59 follow-up: extension + declared Content-Type are both
# client-supplied and spoofable together (rename a .exe to .pdf, send a
# matching fake header). Magic bytes come from the file's actual content,
# so a mismatch here can't be faked by the client the same way. DOCX is a
# ZIP container, so its signature is the generic ZIP one - good enough to
# catch "not actually a PDF or DOCX", not meant to fully validate OOXML
# structure.
MAGIC_BYTES_BY_EXTENSION = {
    ".pdf": b"%PDF-",
    ".docx": b"PK\x03\x04",
}


@router.post("/{document_id}/chunk")
async def chunk_existing_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Chunk an extracted document based on its type."""
    doc = await get_document_for_user(db, document_id, current_user.id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if not doc.extracted_text:
        raise HTTPException(
            status_code=400, detail="Document has no extracted text; run extract first"
        )

    chunks = chunk_document(doc)
    return {
        "id": str(document_id),
        "chunk_count": len(chunks),
        "chunks": chunks,
    }


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    client_id: uuid.UUID = Form(...),
    title: str = Form(...),
    doc_type: DocType = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # RF-78: client_id is caller-supplied - without this check any
    # authenticated user could upload documents under a client they don't
    # own. 404 (not 403) so a client ID can't be probed for existence.
    owned_client = await get_client_for_user(db, client_id, current_user.id)
    if owned_client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    # file.size is populated by Starlette's multipart parser as it spools the
    # upload, so this check happens before create_document's own read()
    # (and before the blob upload it triggers) rather than after.
    if file.size is not None and file.size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 20 MB size limit")

    ext = (
        "." + file.filename.rsplit(".", 1)[-1].lower()
        if file.filename and "." in file.filename
        else ""
    )
    if ext not in ALLOWED_EXTENSIONS or file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415, detail="Only PDF and DOCX files are allowed"
        )

    magic = await file.read(5)
    await file.seek(0)
    if not magic.startswith(MAGIC_BYTES_BY_EXTENSION[ext]):
        raise HTTPException(
            status_code=415,
            detail="File content doesn't match a PDF or DOCX file",
        )

    document = await create_document(
        db=db,
        client_id=client_id,
        user_id=current_user.id,
        title=title,
        doc_type=doc_type,
        file=file,
    )
    # Trigger ingestion via Cloud Run Job (RF-92)
    await trigger_ingestion(str(document.id))

    return DocumentUploadResponse(
        id=document.id,
        title=document.title,
        doc_type=document.doc_type,
        file_name=document.file_name,
        file_size_kb=document.file_size_kb,
        status=document.status,
        created_at=document.created_at,
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document_by_id(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = await get_document_for_user(db, document_id, current_user.id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentDetailResponse.model_validate(document)


@router.post("/{document_id}/extract")
async def extract_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger text extraction for an uploaded document."""
    # Ownership check first - extract_document_text() itself is unscoped
    # (it's also called by the Celery worker with no user context), so
    # scoping happens here at the HTTP boundary instead of in the shared
    # function.
    if await get_document_for_user(db, document_id, current_user.id) is None:
        raise HTTPException(status_code=404, detail="Document not found")

    text = await extract_document_text(document_id, db)
    if text is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found or could not be extracted",
        )
    return {
        "id": str(document_id),
        "extracted": True,
        "char_count": len(text),
        "preview": text[:500] + ("..." if len(text) > 500 else ""),
    }


@router.post("/{document_id}/tag")
async def tag_existing_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger auto-tagging via DeepSeek for an extracted document."""
    # Same reasoning as extract_document above: tag_document() is shared
    # with the worker's unscoped ingestion path, so ownership is checked
    # here instead.
    if await get_document_for_user(db, document_id, current_user.id) is None:
        raise HTTPException(status_code=404, detail="Document not found")

    tags = await tag_document(document_id, db)
    if tags is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found or has no extracted text",
        )
    return {"id": str(document_id), "tags": tags}


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_upload_status(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if await get_document_for_user(db, document_id, current_user.id) is None:
        raise HTTPException(status_code=404, detail="Document not found")

    status = await get_document_status(db, document_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentStatusResponse(**status)


@router.post("/{document_id}/reingest")
async def reingest_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Wipe this document's existing chunks/Qdrant points and re-run
    ingestion, so re-processing an already-ingested document doesn't leave
    the old vectors behind alongside the new ones."""
    document = await get_document_for_user(db, document_id, current_user.id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    await delete_document_vectors_and_chunks(db, document)
    await trigger_ingestion(str(document.id))

    return {"id": str(document_id), "status": "queued"}
