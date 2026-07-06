from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.clients.router import router as clients_router
from app.modules.recruiter.router import router as recruiter_router
from app.modules.candidate.router import router as candidate_router
from app.modules.documents.router import router as documents_router
from app.modules.jobs.router import router as jobs_router
from app.modules.rag.router import router as rag_router
from app.modules.chat.router import router as chat_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(clients_router, prefix="/clients", tags=["clients"])
api_router.include_router(recruiter_router, prefix="/recruiters", tags=["recruiters"])
api_router.include_router(candidate_router, prefix="/candidates", tags=["candidates"])
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
api_router.include_router(rag_router, prefix="/rag", tags=["rag"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])


@api_router.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
