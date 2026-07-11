"""RAG agent tools implemented as LlamaIndex FunctionTools.

Tools:
- search_documents: hybrid search across all ingested documents
- get_document_by_id: fetch a specific document by ID
- generate_document: stream a new document via GLM 5.2 (DeepInfra) RAG
- score_resume: score a resume against a job description
- list_candidates: list candidates matching filters

RF-68 note: search_documents_fn/list_candidates_fn take client_id as a
plain tool parameter, which today an LLM agent would fill in from
conversation context - not currently reachable from any live endpoint
(chat/router.py is still a stub), but whoever wires these into a real
chat agent MUST bind client_id server-side (from an already-ownership-
checked value, same pattern as rag/router.py's /search endpoint) rather
than trust the LLM's tool-call arguments, which an ingested document's
content could influence via prompt injection.
"""

import json
import logging

from llama_index.core.tools import FunctionTool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.llm import complete
from app.modules.documents.models import Document
from app.modules.rag.retriever import hybrid_search, semantic_search

logger = logging.getLogger(__name__)


async def _get_db() -> AsyncSession:  # noqa: ANN201
    """Get a new async DB session."""
    async with async_session_factory() as session:
        return session


# ---------------------------------------------------------------------------
# Tool 1: search_documents
# ---------------------------------------------------------------------------


async def search_documents_fn(
    query: str, client_id: str, doc_type: str | None = None, limit: int = 10
) -> str:
    """Search across all ingested documents using hybrid retrieval (keyword + semantic).

    Args:
        query: The search query string
        client_id: UUID of the client (tenant) to scope results to
        doc_type: Optional filter by document type (resume, job_description, policy, etc.)
        limit: Maximum number of results to return (default 10)

    Returns:
        JSON string with search results
    """
    async with async_session_factory() as db:
        result = await hybrid_search(db, query, client_id, doc_type, limit)
    return json.dumps(result, default=str)


search_documents_tool = FunctionTool.from_defaults(
    async_fn=search_documents_fn,
    name="search_documents",
    description="Search across all ingested documents using hybrid keyword and semantic retrieval. "
    "Returns ranked results with document IDs, titles, and relevance scores. "
    "Always requires a client_id for tenant isolation.",
)


# ---------------------------------------------------------------------------
# Tool 2: get_document_by_id
# ---------------------------------------------------------------------------


async def get_document_by_id_fn(doc_id: str) -> str:
    """Fetch a single document's full details by its ID.

    Args:
        doc_id: The UUID of the document to fetch

    Returns:
        JSON string with all document fields including extracted text
    """
    async with async_session_factory() as db:
        result = await db.execute(
            select(Document).where(Document.id == doc_id, Document.deleted_at.is_(None))
        )
        doc = result.scalar_one_or_none()
        if doc is None:
            return json.dumps({"error": f"Document {doc_id} not found"})
        return json.dumps(
            {
                "id": str(doc.id),
                "title": doc.title,
                "doc_type": doc.doc_type,
                "file_name": doc.file_name,
                "extracted_text": (doc.extracted_text or "")[:5000],
                "auto_tags": doc.auto_tags,
                "created_at": str(doc.created_at),
            },
            default=str,
        )


get_document_by_id_tool = FunctionTool.from_defaults(
    async_fn=get_document_by_id_fn,
    name="get_document_by_id",
    description="Fetch a document's full details including extracted text and auto-tags by its UUID.",
)


# ---------------------------------------------------------------------------
# Tool 3: generate_document (streaming via GLM 5.2 / DeepInfra)
# ---------------------------------------------------------------------------


async def generate_document_fn(
    doc_type: str, context: str, reference_ids: list[str] | None = None
) -> str:
    """Generate a new document using GLM 5.2 (DeepInfra) with RAG context.

    Args:
        doc_type: The type of document to generate (resume, job_description, offer_letter, sop, etc.)
        context: Context description or instructions for the document generation
        reference_ids: Optional list of document UUIDs to use as reference material

    Returns:
        The generated document text
    """
    reference_text = ""
    if reference_ids:
        async with async_session_factory() as db:
            for ref_id in reference_ids:
                result = await db.execute(
                    select(Document).where(
                        Document.id == ref_id, Document.deleted_at.is_(None)
                    )
                )
                ref_doc = result.scalar_one_or_none()
                if ref_doc and ref_doc.extracted_text:
                    reference_text += f"\n--- Reference: {ref_doc.title} ---\n{ref_doc.extracted_text[:3000]}\n"

    system_prompt = (
        f"You are a professional document writer. Generate a high-quality {doc_type} "
        f"based on the context provided. Use the reference documents for style and content inspiration."
    )

    user_prompt = (
        f"Context: {context}\n\nReference material:\n{reference_text}"
        if reference_text
        else f"Context: {context}"
    )
    user_prompt += "\n\nGenerate the complete document with proper formatting."

    return await complete(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=4096,
    )


generate_document_tool = FunctionTool.from_defaults(
    async_fn=generate_document_fn,
    name="generate_document",
    description="Generate a new document (resume, JD, offer letter, SOP, etc.) using AI with optional reference documents. "
    "Provide doc_type, context description, and optional reference document IDs.",
)


# ---------------------------------------------------------------------------
# Tool 4: score_resume
# ---------------------------------------------------------------------------


async def score_resume_fn(resume_id: str, jd_id: str) -> str:
    """Score a resume document against a job description document.

    Args:
        resume_id: UUID of the resume document
        jd_id: UUID of the job description document

    Returns:
        JSON string with scoring breakdown
    """
    async with async_session_factory() as db:
        resume_result = await db.execute(
            select(Document).where(
                Document.id == resume_id, Document.deleted_at.is_(None)
            )
        )
        jd_result = await db.execute(
            select(Document).where(Document.id == jd_id, Document.deleted_at.is_(None))
        )
        resume = resume_result.scalar_one_or_none()
        jd = jd_result.scalar_one_or_none()

    if not resume or not jd:
        return json.dumps({"error": "Resume or Job Description not found"})

    prompt = (
        f"Score the following resume against the job description. "
        f"Provide a JSON response with: overall_score (0-100), skills_match (list of matched skills), "
        f"missing_skills (list), experience_relevance (0-100), education_match (bool), recommendation (strong/medium/weak).\n\n"
        f"Job Description:\n{(jd.extracted_text or '')[:3000]}\n\n"
        f"Resume:\n{(resume.extracted_text or '')[:3000]}"
    )

    return await complete(
        messages=[
            {
                "role": "system",
                "content": "You are an AI resume scorer. Return only valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=1024,
    )


score_resume_tool = FunctionTool.from_defaults(
    async_fn=score_resume_fn,
    name="score_resume",
    description="Score a resume (by document ID) against a job description (by document ID). "
    "Returns skills match, experience relevance, education match, and recommendation.",
)


# ---------------------------------------------------------------------------
# Tool 5: list_candidates
# ---------------------------------------------------------------------------


async def list_candidates_fn(
    client_id: str,
    skills: list[str] | None = None,
    min_experience: int | None = None,
    location: str | None = None,
    limit: int = 20,
) -> str:
    """List candidates matching given filters using semantic search over resumes.

    Args:
        client_id: UUID of the client (tenant) to scope results to
        skills: Optional list of required skills
        min_experience: Optional minimum years of experience
        location: Optional location filter
        limit: Maximum number of results (default 20)

    Returns:
        JSON string with matching candidates
    """
    qdrant_filter: dict[str, str | list[str]] = {"client_id": client_id}
    query_parts = []

    if skills:
        query_parts.extend(skills)
        qdrant_filter["skills"] = skills
    if min_experience:
        query_parts.append(f"{min_experience}+ years experience")
    if location:
        query_parts.append(location)

    query = " ".join(query_parts) if query_parts else "candidate resume"

    results = semantic_search(
        query=query, client_id=client_id, doc_type="resume", limit=limit
    )

    candidates = []
    for r in results:
        payload = r.get("payload", {})
        candidates.append(
            {
                "doc_id": r["id"],
                "candidate_name": payload.get("candidate_name"),
                "skills": payload.get("skills", []),
                "score": r["score"],
            }
        )

    return json.dumps({"total": len(candidates), "candidates": candidates}, default=str)


list_candidates_tool = FunctionTool.from_defaults(
    async_fn=list_candidates_fn,
    name="list_candidates",
    description="List candidates matching filters like skills, experience, and location. "
    "Uses semantic search over resume documents. Always requires a client_id.",
)


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

ALL_TOOLS = [
    search_documents_tool,
    get_document_by_id_tool,
    generate_document_tool,
    score_resume_tool,
    list_candidates_tool,
]
