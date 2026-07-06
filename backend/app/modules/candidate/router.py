from fastapi import APIRouter, Depends

from app.modules.auth.models import User
from app.modules.auth.service import get_current_user

router = APIRouter()


@router.get("/")
async def list_candidates(current_user: User = Depends(get_current_user)):
    return {"message": "Candidates list endpoint"}
