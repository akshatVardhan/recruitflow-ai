from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.qdrant import get_collections_status
from app.modules.auth.models import User
from app.modules.auth.service import get_current_user
from app.modules.rag.retriever import hybrid_search

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    client_id: str
    doc_type: str | None = None
    limit: int = 10


@router.get("/collections")
async def list_collections(current_user: User = Depends(get_current_user)):
    """Return status of all configured Qdrant collections."""
    status = await get_collections_status()
    return {"collections": status}


@router.post("/search")
async def search_documents(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hybrid search across documents using keyword FTS + semantic Qdrant search."""
    result = await hybrid_search(
        db=db,
        query=request.query,
        client_id=request.client_id,
        doc_type=request.doc_type,
        limit=request.limit,
    )
    return result
