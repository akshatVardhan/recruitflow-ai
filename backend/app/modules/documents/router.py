import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.documents.schemas import DocType, DocumentDetailResponse, DocumentStatusResponse, DocumentUploadResponse
from app.modules.documents.service import create_document, get_document, get_document_status

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    client_id: uuid.UUID = Form(...),
    title: str = Form(...),
    doc_type: DocType = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.uuid4()  # placeholder until auth is implemented
    document = await create_document(
        db=db,
        client_id=client_id,
        user_id=user_id,
        title=title,
        doc_type=doc_type,
        file=file,
    )
    return DocumentUploadResponse(
        id=document.id,
        title=document.title,
        doc_type=document.doc_type,
        file_name=document.file_name,
        file_size_kb=document.file_size_kb,
        status="uploaded",
        created_at=document.created_at,
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document_by_id(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    document = await get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentDetailResponse.model_validate(document)


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_upload_status(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    status = await get_document_status(db, document_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentStatusResponse(**status)
