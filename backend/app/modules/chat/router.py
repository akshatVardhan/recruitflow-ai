from fastapi import APIRouter, Depends

from app.modules.auth.models import User
from app.modules.auth.service import get_current_user

router = APIRouter()


@router.post("/stream")
async def chat_stream(current_user: User = Depends(get_current_user)):
    return {"message": "Chat stream endpoint"}
