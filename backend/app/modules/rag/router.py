from fastapi import APIRouter

from app.core.qdrant import get_collections_status

router = APIRouter()


@router.get("/collections")
async def list_collections():
    """Return status of all configured Qdrant collections."""
    status = await get_collections_status()
    return {"collections": status}


@router.post("/search")
async def search_documents():
    return {"message": "Search endpoint"}
