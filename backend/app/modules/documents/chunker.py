"""Chunking strategies for different document types."""

import math
import re
import uuid
from typing import Any

from app.modules.documents.models import Document

# Approximate tokens from characters (4 chars per token on average)
CHARS_PER_TOKEN = 4

# Default paragraph chunk settings
PARAGRAPH_CHUNK_TOKENS = 512
PARAGRAPH_CHUNK_OVERLAP_TOKENS = 50
PARAGRAPH_CHUNK_CHARS = PARAGRAPH_CHUNK_TOKENS * CHARS_PER_TOKEN
PARAGRAPH_OVERLAP_CHARS = PARAGRAPH_CHUNK_OVERLAP_TOKENS * CHARS_PER_TOKEN

# Section headers for resume chunking
RESUME_SECTIONS = [
    "education",
    "experience",
    "work experience",
    "employment",
    "skills",
    "technical skills",
    "certifications",
    "projects",
    "publications",
    "summary",
    "objective",
    "profile",
]

# Section headers for JD chunking
JD_SECTIONS = [
    "role",
    "about the role",
    "job description",
    "requirements",
    "responsibilities",
    "qualifications",
    "what we look for",
    "about you",
    "benefits",
    "location",
]


def _find_section_boundaries(
    text: str, section_keywords: list[str]
) -> list[tuple[int, int, str]]:
    """Find section boundaries in text based on keyword headers.
    Returns list of (start_pos, end_pos, section_name).
    """
    lines = text.split("\n")
    sections: list[tuple[int, str]] = []

    # Find section header positions
    for i, line in enumerate(lines):
        stripped = line.strip().lower().rstrip(":")
        if stripped in section_keywords:
            sections.append((i, line.strip()))

    # If no sections found, treat entire text as one section
    if not sections:
        return [(0, len(text), "full_text")]

    # Map each section to its text range
    boundaries: list[tuple[int, int, str]] = []
    for idx, (line_num, header) in enumerate(sections):
        start_char = sum(len(l) + 1 for l in lines[:line_num])
        if idx + 1 < len(sections):
            end_line = sections[idx + 1][0]
            end_char = sum(len(l) + 1 for l in lines[:end_line])
        else:
            end_char = len(text)
        boundaries.append((start_char, end_char, header))

    return boundaries


def chunk_resume(text: str, doc_id: uuid.UUID) -> list[dict[str, Any]]:
    """Chunk resume text by section."""
    boundaries = _find_section_boundaries(text, RESUME_SECTIONS)
    chunks: list[dict[str, Any]] = []
    for idx, (start, end, section_name) in enumerate(boundaries):
        section_text = text[start:end].strip()
        if section_text:
            chunks.append(
                {
                    "chunk_index": idx,
                    "chunk_text": section_text,
                    "document_id": doc_id,
                    "section": section_name,
                }
            )
    return chunks if chunks else _chunk_by_paragraphs(text, doc_id)


def chunk_job_description(text: str, doc_id: uuid.UUID) -> list[dict[str, Any]]:
    """Chunk job description text by section."""
    boundaries = _find_section_boundaries(text, JD_SECTIONS)
    chunks: list[dict[str, Any]] = []
    for idx, (start, end, section_name) in enumerate(boundaries):
        section_text = text[start:end].strip()
        if section_text:
            chunks.append(
                {
                    "chunk_index": idx,
                    "chunk_text": section_text,
                    "document_id": doc_id,
                    "section": section_name,
                }
            )
    return chunks if chunks else _chunk_by_paragraphs(text, doc_id)


def _chunk_by_paragraphs(text: str, doc_id: uuid.UUID) -> list[dict[str, Any]]:
    """Chunk text by paragraphs with token-size limit and overlap.

    For documents that do not have clear section headers (SOPs, offers, policies, etc.).
    Each paragraph is a logical block. Merged until we hit the token limit,
    then overlapped by the overlap amount.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    if not paragraphs:
        return []

    chunks: list[dict[str, Any]] = []
    current_text = ""
    current_len = 0
    chunk_idx = 0

    for para in paragraphs:
        para_len = len(para)

        # If adding this para exceeds the limit, save current chunk and start new
        if current_text and current_len + para_len + 2 > PARAGRAPH_CHUNK_CHARS:
            chunks.append(
                {
                    "chunk_index": chunk_idx,
                    "chunk_text": current_text.strip(),
                    "document_id": doc_id,
                }
            )
            chunk_idx += 1

            # Overlap: keep last portion of current_text as overlap
            overlap_text = (
                current_text[-PARAGRAPH_OVERLAP_CHARS:]
                if len(current_text) > PARAGRAPH_OVERLAP_CHARS
                else current_text
            )
            current_text = overlap_text + "\n\n" + para if overlap_text else para
            current_len = len(current_text)
        else:
            current_text = (current_text + "\n\n" + para) if current_text else para
            current_len = len(current_text)

    # Last chunk
    if current_text.strip():
        chunks.append(
            {
                "chunk_index": chunk_idx,
                "chunk_text": current_text.strip(),
                "document_id": doc_id,
            }
        )

    return chunks


def chunk_document(document: Document) -> list[dict[str, Any]]:
    """Chunk a document based on its type using the appropriate strategy.

    Returns a list of chunk dicts with chunk_index, chunk_text, document_id.
    """
    text = document.extracted_text or ""
    if not text.strip():
        return []

    doc_type = document.doc_type.lower().replace(" ", "_")
    doc_id = document.id

    if doc_type == "resume":
        return chunk_resume(text, doc_id)
    elif doc_type in ("job_description", "jd"):
        return chunk_job_description(text, doc_id)
    else:
        return _chunk_by_paragraphs(text, doc_id)
