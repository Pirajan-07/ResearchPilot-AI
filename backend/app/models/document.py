"""
ResearchPilot AI — Domain Models: Document State

These are pure Python dataclasses (not Pydantic) — used internally by services.
They are converted to Pydantic schemas before being sent to the API layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


class ProcessingStatus(str, Enum):
    """Five-stage ingestion pipeline status."""
    UPLOADED = "uploaded"
    EXTRACTING = "extracting"
    CHUNKING = "chunking"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class StageStatus:
    """Tracks one named stage of the ingestion pipeline."""
    name: str
    status: str           # "pending" | "running" | "completed" | "failed"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    def mark_running(self) -> None:
        self.status = "running"
        self.started_at = datetime.now(timezone.utc)

    def mark_done(self) -> None:
        self.status = "completed"
        self.completed_at = datetime.now(timezone.utc)

    def mark_failed(self, error: str) -> None:
        self.status = "failed"
        self.completed_at = datetime.now(timezone.utc)
        self.error = error


@dataclass
class DocumentChunk:
    """
    A single text chunk produced by the chunking pipeline.
    Contains all metadata needed for later RAG retrieval and citation.
    """
    chunk_id: str            # "{document_id}_chunk_{index:04d}"
    document_id: str
    text: str
    page_number: int         # 1-indexed, from PyMuPDF
    chunk_index: int         # position within the document's chunk list
    source_filename: str     # original filename (for citation display only)


@dataclass
class ExtractedPage:
    """A single cleaned page from PyMuPDF extraction."""
    page_number: int         # 1-indexed
    text: str                # cleaned text content


@dataclass
class DocumentState:
    """
    In-memory state for a single uploaded document.
    Lives in the DocumentService registry for the lifetime of the server process.
    NOTE: State is intentionally in-memory for MVP — lost on server restart.
    """
    document_id: str
    filename: str             # original display filename (never used for FS paths)
    file_path: str            # absolute path on server FS (uses document_id, not filename)
    status: ProcessingStatus
    stages: List[StageStatus]
    page_count: int = 0
    chunk_count: int = 0
    chunks: List[DocumentChunk] = field(default_factory=list)
    summary: Optional[dict] = None
    insights: Optional[dict] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    @classmethod
    def create_new(cls, document_id: str, filename: str, file_path: str) -> "DocumentState":
        """Factory: create a fresh DocumentState with all pipeline stages pending."""
        stages = [
            StageStatus(name="upload", status="completed"),     # Already done
            StageStatus(name="extraction", status="pending"),
            StageStatus(name="chunking", status="pending"),
            StageStatus(name="indexing", status="pending"),
        ]
        return cls(
            document_id=document_id,
            filename=filename,
            file_path=file_path,
            status=ProcessingStatus.UPLOADED,
            stages=stages,
        )

    def get_stage(self, name: str) -> Optional[StageStatus]:
        for s in self.stages:
            if s.name == name:
                return s
        return None
