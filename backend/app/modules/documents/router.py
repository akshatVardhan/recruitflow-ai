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
    get_document_for_user,
    get_document_status,
)
from app.worker import ingest_document

router = APIRouter()


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

    document = await create_document(
        db=db,
        client_id=client_id,
        user_id=current_user.id,
        title=title,
        doc_type=doc_type,
        file=file,
    )
    # Trigger async ingestion via Celery
    ingest_document.delay(str(document.id))

    return DocumentUploadResponse(
        id=document.id,
        title=document.title,
        doc_type=document.doc_type,
        file_name=document.file_name,
        file_size_kb=document.file_size_kb,
        status="processing",
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
