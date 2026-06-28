from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_recruiters():
    return {"message": "Recruiters list endpoint"}
