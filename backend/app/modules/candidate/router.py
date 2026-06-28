from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_candidates():
    return {"message": "Candidates list endpoint"}
