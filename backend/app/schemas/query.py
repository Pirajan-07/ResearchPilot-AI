"""
ResearchPilot AI — API Schemas: Q&A / RAG

Pydantic models for the Phase 4 grounded Q&A endpoint.
Separate from document schemas to keep each file focused.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    """Request body for POST /api/documents/{id}/query."""
    question: str = Field(..., min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("question must not be empty or whitespace-only.")
        return stripped


class SourceReference(BaseModel):
    """
    A single source chunk cited in a Q&A answer.
    Carries page-level provenance for frontend display.
    """
    chunk_id: str
    page_number: int
    source_filename: str
    excerpt: str       # Short passage from the chunk used to support the answer


class QueryResponse(BaseModel):
    """Response returned by POST /api/documents/{id}/query."""
    document_id: str
    question: str
    answer: str
    sources: List[SourceReference]


# ── Internal Pydantic schema for Gemini structured output ─────────────────────
# These are NOT returned directly to the client — they are parsed and
# converted to QueryResponse / SourceReference above.

class _InternalSourceRef(BaseModel):
    """Gemini structured-output source reference."""
    chunk_id: str = Field(
        description="Exact chunk_id from the provided document excerpts."
    )
    page_number: int = Field(
        description="Page number where this excerpt appears in the document."
    )
    source_filename: str = Field(
        description="Name of the source PDF file."
    )
    excerpt: str = Field(
        description=(
            "A short, verbatim or near-verbatim passage from the chunk "
            "that directly supports the answer. Keep under 200 characters."
        )
    )


class _InternalRAGAnswer(BaseModel):
    """
    Gemini structured-output schema for grounded research Q&A.
    Used with ChatGoogleGenerativeAI.with_structured_output().
    """
    answer: str = Field(
        description=(
            "Answer to the question based SOLELY on the provided document excerpts. "
            "If the answer cannot be found in the excerpts, state clearly: "
            "'The provided document excerpts do not contain enough information to answer this question.'"
        )
    )
    sources: List[_InternalSourceRef] = Field(
        default=[],
        description=(
            "List of source chunks actually used to generate the answer. "
            "Include only chunks that are genuinely referenced. "
            "If the answer is 'not found', this list should be empty."
        )
    )
