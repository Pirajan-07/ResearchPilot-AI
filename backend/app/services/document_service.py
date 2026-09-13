"""
ResearchPilot AI — Document Service

Central orchestrator for the PDF ingestion pipeline.

Responsibilities:
  1. Validate uploaded file (MIME type, extension, size)
  2. Save file to the upload directory using only document_id as the filename
     (never trusts the original filename for filesystem paths — prevents path traversal)
  3. Manage the in-memory DocumentState registry
  4. Run the ingestion pipeline as a background task:
       upload → extraction → chunking → completed (or failed)

State is intentionally kept in-memory for the MVP. On server restart, all state
is lost. The frontend handles this gracefully by detecting a 404 status and
presenting the upload UI again.

SECURITY:
  - GEMINI_API_KEY is never accessed in this module.
  - Gemini is NOT called in this module.
  - File paths always use document_id, never original filename.
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Dict, Optional

from loguru import logger

from app.config import settings
from app.models.document import DocumentChunk, DocumentState, ProcessingStatus
from app.services import chunking_service, parser_service
from app.services import indexing_service
from app.services.indexing_service import IndexingError
from app.services.parser_service import EmptyDocumentError, PDFReadError

# ── Allowed MIME types ──────────────────────────────────────────────────────────
_ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/x-pdf",
    "application/acrobat",
    "applications/vnd.pdf",
    "text/pdf",
    "text/x-pdf",
}
_ALLOWED_EXTENSION = ".pdf"
_MAGIC_BYTES = b"%PDF"   # PDF magic bytes — first 4 bytes of every valid PDF


# ── Custom exceptions ───────────────────────────────────────────────────────────

class FileValidationError(Exception):
    """Raised when an uploaded file fails validation (type, size, magic bytes)."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


# ── In-memory state registry ────────────────────────────────────────────────────
# Key: document_id (UUID string)
# Thread-safety note: CPython's GIL makes simple dict reads/writes safe for the
# MVP's single-process uvicorn deployment. A production deployment would use Redis.
_registry: Dict[str, DocumentState] = {}


# ── Public API ──────────────────────────────────────────────────────────────────

def get_document(document_id: str) -> Optional[DocumentState]:
    """Return the DocumentState for a given ID, or None if not found."""
    return _registry.get(document_id)


def list_documents() -> list[DocumentState]:
    """Return all known documents, most-recently-created first."""
    return sorted(_registry.values(), key=lambda d: d.created_at, reverse=True)


async def validate_and_save(
    filename: str,
    content_type: str | None,
    file_bytes: bytes,
) -> DocumentState:
    """
    Validate the uploaded file and persist it to disk.

    Validation checks (in order):
      1. File extension must be .pdf
      2. Content-Type header must be a known PDF MIME type
      3. File must not be empty
      4. File size must not exceed MAX_UPLOAD_SIZE_MB
      5. First 4 bytes must be the PDF magic signature %PDF

    Args:
        filename:     Original filename from the upload (used for display only).
        content_type: Content-Type header from the multipart upload.
        file_bytes:   Raw bytes of the uploaded file.

    Returns:
        A freshly created DocumentState (status=UPLOADED).

    Raises:
        FileValidationError: On any validation failure with an appropriate HTTP status.
    """
    # 1. Extension check
    suffix = Path(filename).suffix.lower()
    if suffix != _ALLOWED_EXTENSION:
        raise FileValidationError(
            f"Invalid file type. Only PDF files are accepted (got '{suffix}').",
            status_code=415,
        )

    # 2. Content-Type check
    if content_type:
        # Strip parameters like "; charset=utf-8"
        mime = content_type.split(";")[0].strip().lower()
        if mime not in _ALLOWED_CONTENT_TYPES:
            raise FileValidationError(
                f"Invalid Content-Type '{mime}'. Expected a PDF MIME type.",
                status_code=415,
            )

    # 3. Empty file check
    if not file_bytes:
        raise FileValidationError("Uploaded file is empty.", status_code=400)

    # 4. Size check
    size_bytes = len(file_bytes)
    max_bytes = settings.max_upload_size_bytes
    if size_bytes > max_bytes:
        raise FileValidationError(
            f"File too large ({size_bytes / 1_048_576:.1f} MB). "
            f"Maximum allowed size is {settings.MAX_UPLOAD_SIZE_MB} MB.",
            status_code=413,
        )

    # 5. Magic bytes check (first 4 bytes must be "%PDF")
    if not file_bytes[:4].startswith(_MAGIC_BYTES):
        raise FileValidationError(
            "File does not appear to be a valid PDF (magic bytes check failed).",
            status_code=400,
        )

    # Generate a secure document ID
    document_id = str(uuid.uuid4())

    # Save file — path uses document_id, NEVER the original filename
    upload_dir: Path = settings.UPLOAD_DIR
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{document_id}.pdf"

    try:
        file_path.write_bytes(file_bytes)
    except OSError as exc:
        logger.error("Failed to save uploaded file: {}", exc)
        raise FileValidationError(
            "Failed to save the uploaded file. Please try again.",
            status_code=500,
        ) from exc

    logger.info(
        "Saved upload — document_id={}, original_name='{}', size={:.1f} KB",
        document_id,
        filename,
        size_bytes / 1024,
    )

    # Create and register DocumentState
    state = DocumentState.create_new(
        document_id=document_id,
        filename=filename,
        file_path=str(file_path),
    )
    _registry[document_id] = state
    return state


async def ingest(document_id: str) -> None:
    """
    Background task: run the full ingestion pipeline for an uploaded document.

    Pipeline stages:
      1. extraction  — PyMuPDF text extraction
      2. chunking    — LangChain RecursiveCharacterTextSplitter
      3. indexing    — HuggingFace embeddings → ChromaDB persistence

    State transitions:
      UPLOADED → EXTRACTING → CHUNKING → INDEXING → COMPLETED
                                                   ↓ (on any error)
                                                 FAILED

    This function is safe to call from FastAPI's BackgroundTasks.
    Gemini is NOT called here.
    """
    state = _registry.get(document_id)
    if state is None:
        logger.error("ingest() called for unknown document_id={}", document_id)
        return

    file_path = Path(state.file_path)

    # ── Stage: Extraction ───────────────────────────────────────────────────────
    extraction_stage = state.get_stage("extraction")
    if extraction_stage:
        extraction_stage.mark_running()
    state.status = ProcessingStatus.EXTRACTING
    logger.info("Starting extraction for document_id={}", document_id)

    try:
        pages = parser_service.extract_pages(file_path)
    except EmptyDocumentError as exc:
        _fail(state, "extraction", str(exc))
        return
    except PDFReadError as exc:
        _fail(state, "extraction", f"PDF read error: {exc}")
        return
    except Exception as exc:
        logger.exception("Unexpected extraction error for document_id={}", document_id)
        _fail(state, "extraction", "Unexpected error during text extraction.")
        return

    state.page_count = len(pages)
    if extraction_stage:
        extraction_stage.mark_done()
    logger.info("Extraction complete: {} pages for document_id={}", len(pages), document_id)

    # ── Stage: Chunking ─────────────────────────────────────────────────────────
    chunking_stage = state.get_stage("chunking")
    if chunking_stage:
        chunking_stage.mark_running()
    state.status = ProcessingStatus.CHUNKING
    logger.info("Starting chunking for document_id={}", document_id)

    try:
        chunks = chunking_service.chunk_pages(
            pages=pages,
            document_id=document_id,
            source_filename=state.filename,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )
    except Exception as exc:
        logger.exception("Unexpected chunking error for document_id={}", document_id)
        _fail(state, "chunking", "Unexpected error during text chunking.")
        return

    state.chunks = chunks
    state.chunk_count = len(chunks)
    if chunking_stage:
        chunking_stage.mark_done()
    logger.info("Chunking complete: {} chunks for document_id={}", len(chunks), document_id)

    # ── Stage: Indexing ─────────────────────────────────────────────────────────
    indexing_stage = state.get_stage("indexing")
    if indexing_stage:
        indexing_stage.mark_running()
    state.status = ProcessingStatus.INDEXING
    logger.info("Starting ChromaDB indexing for document_id={}", document_id)

    try:
        result = indexing_service.index_document(
            document_id=document_id,
            chunks=chunks,
            chroma_dir=settings.CHROMA_PERSIST_DIRECTORY,
        )
        # Chunks are now persisted in ChromaDB; clear from in-memory state to save RAM
        # They remain accessible via indexing_service.search_document()
        state.chunks = []
    except IndexingError as exc:
        _fail(state, "indexing", str(exc))
        return
    except Exception as exc:
        logger.exception("Unexpected indexing error for document_id={}", document_id)
        _fail(state, "indexing", "Unexpected error during vector indexing.")
        return

    if indexing_stage:
        indexing_stage.mark_done()
    logger.info(
        "Indexing complete: {} chunks persisted for document_id={}",
        result.chunks_indexed,
        document_id,
    )

    # ── Pipeline complete ───────────────────────────────────────────────────────
    from datetime import datetime, timezone
    state.status = ProcessingStatus.COMPLETED
    state.completed_at = datetime.now(timezone.utc)
    logger.info("Ingestion COMPLETED for document_id={}", document_id)


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _fail(state: DocumentState, failing_stage: str, error_message: str) -> None:
    """Mark a stage and the overall document as failed."""
    stage = state.get_stage(failing_stage)
    if stage:
        stage.mark_failed(error_message)
    state.status = ProcessingStatus.FAILED
    state.error = error_message
    logger.error(
        "Ingestion FAILED at '{}' for document_id={}: {}",
        failing_stage,
        state.document_id,
        error_message,
    )
