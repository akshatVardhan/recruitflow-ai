from fastapi import APIRouter

router = APIRouter()


@router.post("/login")
async def login():
    return {"message": "Login endpoint"}


@router.post("/refresh")
async def refresh():
    return {"message": "Refresh endpoint"}
