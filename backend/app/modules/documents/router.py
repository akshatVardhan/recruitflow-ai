from fastapi import APIRouter

router = APIRouter()


@router.post("/upload")
async def upload_document():
    return {"message": "Upload endpoint"}


@router.get("/{document_id}/status")
async def get_document_status(document_id: str):
    return {"message": f"Status for {document_id}"}
