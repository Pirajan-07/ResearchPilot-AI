"""
ResearchPilot AI — API Schemas: Document

Pydantic models used in request/response serialization.
These are separate from the internal domain models (app/models/document.py).
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class UploadResponse(BaseModel):
    """Response returned immediately after a successful file upload."""
    document_id: str
    filename: str
    status: str
    message: str


class StageStatusSchema(BaseModel):
    """Serialisable representation of one pipeline stage."""
    name: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    model_config = {"from_attributes": True}


class DocumentStatusResponse(BaseModel):
    """Full document state — returned by the status polling endpoint."""
    document_id: str
    filename: str
    status: str
    page_count: int
    chunk_count: int
    stages: List[StageStatusSchema]
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    has_summary: bool = False
    has_insights: bool = False

    model_config = {"from_attributes": True}


class ErrorResponse(BaseModel):
    """Standard error shape returned by all error responses."""
    error: str
    detail: Optional[str] = None


class SearchRequest(BaseModel):
    """Request body for the semantic search endpoint."""
    query: str
    top_k: Optional[int] = None   # Defaults to settings.RETRIEVAL_TOP_K if not provided


class RetrievalResultResponse(BaseModel):
    """A single chunk returned by the semantic search endpoint."""
    chunk_id: str
    document_id: str
    page_number: int
    source_filename: str
    text: str
    score: float
