import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.qdrant import get_collections_status
from app.modules.auth.models import User
from app.modules.auth.service import get_current_user
from app.modules.clients.service import get_client_for_user
from app.modules.rag.retriever import hybrid_search

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    client_id: uuid.UUID
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
    # ADR-009: tenancy is a per-request ownership check, not a JWT claim - a
    # user can own multiple clients, so client_id travels with the request
    # and must be verified here, same pattern as documents/router.py's
    # upload endpoint (RF-78). 404 (not 403) so a client ID can't be probed
    # for existence.
    owned_client = await get_client_for_user(db, request.client_id, current_user.id)
    if owned_client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    result = await hybrid_search(
        db=db,
        query=request.query,
        client_id=str(request.client_id),
        doc_type=request.doc_type,
        limit=request.limit,
    )
    return result
