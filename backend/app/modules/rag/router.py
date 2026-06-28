from fastapi import APIRouter

router = APIRouter()


@router.post("/search")
async def search_documents():
    return {"message": "Search endpoint"}
