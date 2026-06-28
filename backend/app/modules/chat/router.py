from fastapi import APIRouter

router = APIRouter()


@router.post("/stream")
async def chat_stream():
    return {"message": "Chat stream endpoint"}
