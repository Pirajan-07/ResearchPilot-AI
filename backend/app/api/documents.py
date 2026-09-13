"""
ResearchPilot AI — Documents API Router

Endpoints:
  POST /api/documents              Upload a PDF and start ingestion pipeline
  GET  /api/documents              List all known documents
  GET  /api/documents/{id}         Get document status (for polling)
  DELETE /api/documents/{id}       Delete a document and its file
  POST /api/documents/{id}/search  Semantic search within an indexed document
  POST /api/documents/{id}/query   Grounded Q&A via Gemini (Phase 4)

SECURITY:
  - GEMINI_API_KEY is never exposed to the browser.
  - File paths are never exposed to the client.
  - Stack traces are never returned to the client.
  - Path traversal is prevented in document_service.validate_and_save().
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile

from app.config import settings
from app.schemas.document import (
    DocumentStatusResponse,
    ErrorResponse,
    RetrievalResultResponse,
    SearchRequest,
    StageStatusSchema,
    UploadResponse,
)
from app.schemas.query import QueryRequest, QueryResponse
from app.services import document_service
from app.services import indexing_service
from app.services import rag_service
from app.services.document_service import FileValidationError
from app.services.indexing_service import RetrievalError
from app.services.rag_service import (
    RAGConfigurationError,
    RAGGenerationError,
    RAGRetrievalError,
)
from app.schemas.analysis import PaperSummaryResponse, PaperInsightsResponse
from app.services import analysis_service
from app.services.analysis_service import AnalysisConfigurationError, AnalysisGenerationError

router = APIRouter()


# ── POST /api/documents ─────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=UploadResponse,
    status_code=202,
    summary="Upload a PDF and start ingestion",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file"},
        413: {"model": ErrorResponse, "description": "File too large"},
        415: {"model": ErrorResponse, "description": "Unsupported file type"},
    },
)
async def upload_document(
    file: UploadFile,
    background_tasks: BackgroundTasks,
) -> UploadResponse:
    """
    Upload a PDF file and begin the ingestion pipeline.

    The response is returned immediately (HTTP 202 Accepted) before ingestion
    completes. Poll GET /api/documents/{id} to track progress.

    Validation performed before accepting the file:
    - Extension must be .pdf
    - Content-Type must be a PDF MIME type
    - File must not exceed the configured maximum size
    - File must begin with the PDF magic bytes (%PDF)
    """
    try:
        file_bytes = await file.read()
        state = await document_service.validate_and_save(
            filename=file.filename or "upload.pdf",
            content_type=file.content_type,
            file_bytes=file_bytes,
        )
    except FileValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    # Kick off pipeline as a background task — returns immediately to the client
    background_tasks.add_task(document_service.ingest, state.document_id)

    return UploadResponse(
        document_id=state.document_id,
        filename=state.filename,
        status=state.status.value,
        message=(
            "File accepted. Ingestion pipeline started. "
            f"Poll GET /api/documents/{state.document_id} for status."
        ),
    )


# ── GET /api/documents ──────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=List[DocumentStatusResponse],
    summary="List all documents",
)
async def list_documents() -> List[DocumentStatusResponse]:
    """Return status for all documents known to this server instance."""
    return [_state_to_response(doc) for doc in document_service.list_documents()]


# ── GET /api/documents/{document_id} ───────────────────────────────────────────

@router.get(
    "/{document_id}",
    response_model=DocumentStatusResponse,
    summary="Get document ingestion status",
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
)
async def get_document_status(document_id: str) -> DocumentStatusResponse:
    """
    Get current status for a specific document.

    Poll this endpoint after uploading to track ingestion progress.
    Status values: uploaded → extracting → chunking → completed | failed
    """
    state = document_service.get_document(document_id)
    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' not found. "
                   "Note: document state is in-memory and is lost on server restart.",
        )
    return _state_to_response(state)


# ── DELETE /api/documents/{document_id} ────────────────────────────────────────

@router.delete(
    "/{document_id}",
    status_code=200,
    summary="Delete a document",
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
)
async def delete_document(document_id: str) -> dict:
    """
    Remove a document from memory and delete its file from disk.

    After deletion, any subsequent GET for this document_id will return 404.
    """
    from pathlib import Path
    from loguru import logger

    state = document_service.get_document(document_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    from pathlib import Path
    from loguru import logger

    # 1. Remove ChromaDB vectors (must be first — uses document_id)
    try:
        indexing_service.delete_document_vectors(
            document_id=document_id,
            chroma_dir=settings.CHROMA_PERSIST_DIRECTORY,
        )
    except Exception as exc:
        logger.error("Failed to delete vectors for document_id={}: {}", document_id, exc)
        # Continue — best-effort cleanup

    # 2. Remove the uploaded PDF file from disk
    try:
        file_path = Path(state.file_path)
        if file_path.exists():
            file_path.unlink()
            logger.info("Deleted file for document_id={}", document_id)
    except OSError as exc:
        logger.error("Failed to delete file for document_id={}: {}", document_id, exc)

    # 3. Remove from in-memory registry
    document_service._registry.pop(document_id, None)
    return {"message": f"Document '{document_id}' deleted successfully."}


# ── POST /api/documents/{document_id}/search ────────────────────────────────────

@router.post(
    "/{document_id}/search",
    response_model=List[RetrievalResultResponse],
    summary="Semantic search within a document",
    responses={
        404: {"model": ErrorResponse, "description": "Document not found or not indexed"},
        422: {"model": ErrorResponse, "description": "Invalid search request"},
        500: {"model": ErrorResponse, "description": "Retrieval error"},
    },
)
async def search_document(document_id: str, body: SearchRequest) -> List[RetrievalResultResponse]:
    """
    Perform a semantic similarity search within a single document's indexed chunks.

    Uses the same embedding model as indexing (all-MiniLM-L6-v2, local CPU).
    Returns up to top_k chunks ordered by relevance.

    This endpoint is the retrieval foundation for the Q&A phase.
    Gemini is NOT called here.
    """
    state = document_service.get_document(document_id)
    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' not found.",
        )
    if state.status.value not in ("completed",):
        raise HTTPException(
            status_code=422,
            detail=(
                f"Document is not ready for search (current status: '{state.status.value}'). "
                "Wait until status is 'completed'."
            ),
        )

    top_k = body.top_k if body.top_k is not None else settings.RETRIEVAL_TOP_K

    try:
        results = indexing_service.search_document(
            document_id=document_id,
            query=body.query,
            chroma_dir=settings.CHROMA_PERSIST_DIRECTORY,
            top_k=top_k,
        )
    except RetrievalError as exc:
        raise HTTPException(
            status_code=500,
            detail="Search failed. Please try again or re-upload the document.",
        ) from exc

    return [
        RetrievalResultResponse(
            chunk_id=r.chunk_id,
            document_id=r.document_id,
            page_number=r.page_number,
            source_filename=r.source_filename,
            text=r.text,
            score=r.score,
        )
        for r in results
    ]


# ── POST /api/documents/{document_id}/query ─────────────────────────────────

@router.post(
    "/{document_id}/query",
    response_model=QueryResponse,
    summary="Grounded research Q&A (Gemini)",
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
        422: {"model": ErrorResponse, "description": "Document not ready or invalid question"},
        500: {"model": ErrorResponse, "description": "Retrieval or Gemini failure"},
        503: {"model": ErrorResponse, "description": "Gemini not configured or quota exhausted"},
    },
)
async def query_document(document_id: str, body: QueryRequest) -> QueryResponse:
    """
    Answer a research question grounded in the uploaded paper.

    Flow:
      1. Retrieve relevant chunks from ChromaDB (Phase 3 retrieval service)
      2. Assemble delimited context with page provenance
      3. Send context + question to Gemini via structured-output prompt
      4. Return answer + cited source references

    Gemini is NOT called if the document is not yet fully indexed.
    The API key is never returned in any response.
    """
    # 1. Document must exist
    state = document_service.get_document(document_id)
    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' not found.",
        )

    # 2. Document must be fully indexed
    if state.status.value != "completed":
        raise HTTPException(
            status_code=422,
            detail=(
                f"Document is not ready for Q&A (current status: '{state.status.value}'). "
                "Wait until status is 'completed'."
            ),
        )

    # 3. Execute RAG pipeline
    try:
        response = rag_service.answer_question(
            document_id=document_id,
            question=body.question,
            chroma_dir=settings.CHROMA_PERSIST_DIRECTORY,
            top_k=settings.RETRIEVAL_TOP_K,
        )
    except RAGConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail="Gemini AI is not configured. Please contact the administrator.",
        ) from exc
    except RAGRetrievalError as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve context from the document index. Try re-uploading the document.",
        ) from exc
    except RAGGenerationError as exc:
        raise HTTPException(
            status_code=500,
            detail="AI generation failed. Please try again or check your API quota.",
        ) from exc
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please try again.",
        )

    return response


# ── GET /api/documents/{document_id}/summary ────────────────────────────────

@router.get(
    "/{document_id}/summary",
    response_model=PaperSummaryResponse,
    summary="Get 9-dimension structured paper summary",
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
        422: {"model": ErrorResponse, "description": "Document not ready"},
        500: {"model": ErrorResponse, "description": "Generation failure"},
        503: {"model": ErrorResponse, "description": "Gemini not configured or quota exhausted"},
    },
)
async def get_document_summary(document_id: str) -> PaperSummaryResponse:
    """
    Generate or return the cached 9-dimension paper summary.
    """
    state = document_service.get_document(document_id)
    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' not found.",
        )
    if state.status.value != "completed":
        raise HTTPException(
            status_code=422,
            detail="Document is not ready for analysis.",
        )

    try:
        response = analysis_service.generate_summary(
            document_id=document_id,
            chroma_dir=settings.CHROMA_PERSIST_DIRECTORY,
        )
    except AnalysisConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except AnalysisGenerationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected error during summary generation.")

    return response


# ── GET /api/documents/{document_id}/insights ───────────────────────────────

@router.get(
    "/{document_id}/insights",
    response_model=PaperInsightsResponse,
    summary="Get 7-dimension structured paper insights",
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
        422: {"model": ErrorResponse, "description": "Document not ready"},
        500: {"model": ErrorResponse, "description": "Generation failure"},
        503: {"model": ErrorResponse, "description": "Gemini not configured or quota exhausted"},
    },
)
async def get_document_insights(document_id: str) -> PaperInsightsResponse:
    """
    Generate or return the cached 7-dimension paper insights.
    """
    state = document_service.get_document(document_id)
    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' not found.",
        )
    if state.status.value != "completed":
        raise HTTPException(
            status_code=422,
            detail="Document is not ready for analysis.",
        )

    try:
        response = analysis_service.generate_insights(
            document_id=document_id,
            chroma_dir=settings.CHROMA_PERSIST_DIRECTORY,
        )
    except AnalysisConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except AnalysisGenerationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected error during insights generation.")

    return response


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _state_to_response(state) -> DocumentStatusResponse:
    """Convert internal DocumentState to the API response schema."""
    return DocumentStatusResponse(
        document_id=state.document_id,
        filename=state.filename,
        status=state.status.value,
        page_count=state.page_count,
        chunk_count=state.chunk_count,
        stages=[
            StageStatusSchema(
                name=s.name,
                status=s.status,
                started_at=s.started_at,
                completed_at=s.completed_at,
                error=s.error,
            )
            for s in state.stages
        ],
        created_at=state.created_at,
        completed_at=state.completed_at,
        error=state.error,
        has_summary=state.summary is not None,
        has_insights=state.insights is not None,
    )
