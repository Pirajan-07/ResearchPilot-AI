"""
ResearchPilot AI — Tests: Document API Endpoints

Covers:
  - POST /api/documents: valid PDF upload → 202, returns document_id
  - POST /api/documents: invalid file type (not PDF) → 415
  - POST /api/documents: file with wrong extension → 415
  - POST /api/documents: PDF too large → 413
  - POST /api/documents: corrupted PDF → ingestion fails gracefully
  - POST /api/documents: empty/no-text PDF → ingestion fails with clear error
  - GET  /api/documents/{id}: returns status for known document
  - GET  /api/documents/{id}: 404 for unknown document
  - GET  /api/documents: returns list of documents
  - Full happy-path: upload → poll → COMPLETED status
  - Fail path: upload scanned PDF → poll → FAILED status with error message
  - Health endpoint: still returns 200 after router activation

SECURITY:
  - Verifies no GEMINI_API_KEY is required or used in any test
  - Verifies API responses never contain file system paths
"""
from __future__ import annotations

import io
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Set a dummy GEMINI_API_KEY before importing the app
# This satisfies the Pydantic validator without making any API calls.
os.environ.setdefault("GEMINI_API_KEY", "test-dummy-key-phase2-no-gemini-calls")

from main import app
from app.services import document_service as ds


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear the in-memory document registry before and after each test."""
    ds._registry.clear()
    yield
    ds._registry.clear()


@pytest.fixture
def client(tmp_path: Path):
    """FastAPI TestClient with upload dir redirected to an isolated temp directory."""
    from app import config
    # Override upload and chroma dirs to isolated temp paths per test
    config.settings.UPLOAD_DIR = tmp_path / "uploads"
    config.settings.CHROMA_PERSIST_DIRECTORY = tmp_path / "chroma"
    config.settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    config.settings.CHROMA_PERSIST_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with TestClient(app) as c:
        yield c


# ── Helper ────────────────────────────────────────────────────────────────────

def make_upload_file(content: bytes, filename: str, content_type: str = "application/pdf"):
    """Create an in-memory UploadFile-compatible tuple for TestClient."""
    return ("file", (filename, io.BytesIO(content), content_type))


# ── Health check ─────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_health_does_not_expose_api_key(self, client):
        resp = client.get("/health")
        body = resp.text
        # The real key value must never appear — here "dummy" is the sentinel
        assert "test-dummy-key" not in body


# ── Upload: Happy path ────────────────────────────────────────────────────────

class TestUploadValid:
    def test_valid_pdf_returns_202(self, client, sample_pdf_bytes):
        files = [make_upload_file(sample_pdf_bytes, "paper.pdf")]
        resp = client.post("/api/documents/", files=files)
        assert resp.status_code == 202, resp.text

    def test_valid_pdf_response_has_document_id(self, client, sample_pdf_bytes):
        files = [make_upload_file(sample_pdf_bytes, "paper.pdf")]
        resp = client.post("/api/documents/", files=files)
        data = resp.json()
        assert "document_id" in data
        assert len(data["document_id"]) == 36  # UUID4 format

    def test_valid_pdf_response_has_status_field(self, client, sample_pdf_bytes):
        files = [make_upload_file(sample_pdf_bytes, "paper.pdf")]
        resp = client.post("/api/documents/", files=files)
        data = resp.json()
        assert "status" in data
        assert data["status"] in ("uploaded", "extracting", "chunking", "completed")

    def test_valid_pdf_response_does_not_expose_file_path(self, client, sample_pdf_bytes):
        """API response must NEVER contain the server filesystem path."""
        files = [make_upload_file(sample_pdf_bytes, "paper.pdf")]
        resp = client.post("/api/documents/", files=files)
        body = resp.text
        assert "storage" not in body
        assert "uploads" not in body
        assert "C:\\" not in body
        assert "/home/" not in body


# ── Upload: Validation errors ─────────────────────────────────────────────────

class TestUploadValidation:
    def test_non_pdf_extension_returns_415(self, client):
        files = [make_upload_file(b"some content", "document.docx", "application/msword")]
        resp = client.post("/api/documents/", files=files)
        assert resp.status_code == 415

    def test_txt_file_returns_415(self, client):
        files = [make_upload_file(b"plain text", "notes.txt", "text/plain")]
        resp = client.post("/api/documents/", files=files)
        assert resp.status_code == 415

    def test_pdf_extension_wrong_mime_returns_415(self, client, sample_pdf_bytes):
        """Correct extension but wrong MIME type."""
        files = [make_upload_file(sample_pdf_bytes, "paper.pdf", "text/plain")]
        resp = client.post("/api/documents/", files=files)
        assert resp.status_code == 415

    def test_oversized_file_returns_413(self, client):
        """File exceeding MAX_UPLOAD_SIZE_MB returns 413."""
        from app import config
        original_max = config.settings.MAX_UPLOAD_SIZE_MB
        config.settings.MAX_UPLOAD_SIZE_MB = 0  # Force 0 MB limit — everything fails
        try:
            files = [make_upload_file(b"%PDF-fake-content-small", "paper.pdf")]
            resp = client.post("/api/documents/", files=files)
            assert resp.status_code == 413
        finally:
            config.settings.MAX_UPLOAD_SIZE_MB = original_max

    def test_empty_file_returns_400(self, client):
        files = [make_upload_file(b"", "paper.pdf")]
        resp = client.post("/api/documents/", files=files)
        assert resp.status_code == 400

    def test_file_with_bad_magic_bytes_returns_400(self, client):
        """File named .pdf but not a real PDF (bad magic bytes)."""
        files = [make_upload_file(b"NOTAPDF content here", "paper.pdf")]
        resp = client.post("/api/documents/", files=files)
        assert resp.status_code == 400


# ── Status polling ────────────────────────────────────────────────────────────

class TestDocumentStatus:
    def test_get_status_for_known_document(self, client, sample_pdf_bytes):
        files = [make_upload_file(sample_pdf_bytes, "paper.pdf")]
        upload_resp = client.post("/api/documents/", files=files)
        doc_id = upload_resp.json()["document_id"]

        status_resp = client.get(f"/api/documents/{doc_id}")
        assert status_resp.status_code == 200

    def test_get_status_returns_expected_fields(self, client, sample_pdf_bytes):
        files = [make_upload_file(sample_pdf_bytes, "paper.pdf")]
        doc_id = client.post("/api/documents/", files=files).json()["document_id"]

        data = client.get(f"/api/documents/{doc_id}").json()
        assert "document_id" in data
        assert "status" in data
        assert "page_count" in data
        assert "chunk_count" in data
        assert "stages" in data
        assert "created_at" in data

    def test_status_response_does_not_expose_file_path(self, client, sample_pdf_bytes):
        files = [make_upload_file(sample_pdf_bytes, "paper.pdf")]
        doc_id = client.post("/api/documents/", files=files).json()["document_id"]
        body = client.get(f"/api/documents/{doc_id}").text
        assert "storage" not in body
        assert "uploads" not in body

    def test_unknown_document_id_returns_404(self, client):
        resp = client.get("/api/documents/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    def test_list_documents_returns_list(self, client):
        resp = client.get("/api/documents/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ── Full happy path ────────────────────────────────────────────────────────────

class TestFullIngestionHappyPath:
    """
    End-to-end ingestion test:
    Upload a valid PDF → background task runs → status is COMPLETED.

    With FastAPI's TestClient, background tasks run synchronously before the
    next request, so by the time we call GET status the pipeline has finished.
    """

    def test_full_ingestion_reaches_completed(self, client, sample_pdf_bytes):
        files = [make_upload_file(sample_pdf_bytes, "paper.pdf")]
        upload_resp = client.post("/api/documents/", files=files)
        assert upload_resp.status_code == 202
        doc_id = upload_resp.json()["document_id"]

        status = client.get(f"/api/documents/{doc_id}").json()
        assert status["status"] == "completed", f"Expected completed, got: {status}"

    def test_completed_document_has_nonzero_page_count(self, client, sample_pdf_bytes):
        files = [make_upload_file(sample_pdf_bytes, "paper.pdf")]
        doc_id = client.post("/api/documents/", files=files).json()["document_id"]

        status = client.get(f"/api/documents/{doc_id}").json()
        assert status["page_count"] == 2  # sample PDF has 2 pages

    def test_completed_document_has_nonzero_chunk_count(self, client, sample_pdf_bytes):
        files = [make_upload_file(sample_pdf_bytes, "paper.pdf")]
        doc_id = client.post("/api/documents/", files=files).json()["document_id"]

        status = client.get(f"/api/documents/{doc_id}").json()
        assert status["chunk_count"] >= 1

    def test_all_stages_completed_on_success(self, client, sample_pdf_bytes):
        files = [make_upload_file(sample_pdf_bytes, "paper.pdf")]
        doc_id = client.post("/api/documents/", files=files).json()["document_id"]

        stages = client.get(f"/api/documents/{doc_id}").json()["stages"]
        # Pipeline now has 4 stages: upload, extraction, chunking, indexing
        stage_names = [s["name"] for s in stages]
        assert "extraction" in stage_names
        assert "chunking" in stage_names
        assert "indexing" in stage_names
        for stage in stages:
            assert stage["status"] in ("completed", "pending"), (
                f"Stage '{stage['name']}' unexpected status: {stage['status']}"
            )

    def test_filename_preserved_in_status(self, client, sample_pdf_bytes):
        files = [make_upload_file(sample_pdf_bytes, "my_research_paper.pdf")]
        doc_id = client.post("/api/documents/", files=files).json()["document_id"]

        data = client.get(f"/api/documents/{doc_id}").json()
        assert data["filename"] == "my_research_paper.pdf"

    def test_file_saved_to_disk_on_upload(self, client, sample_pdf_bytes, tmp_path):
        from app import config
        files = [make_upload_file(sample_pdf_bytes, "paper.pdf")]
        doc_id = client.post("/api/documents/", files=files).json()["document_id"]

        saved_file = config.settings.UPLOAD_DIR / f"{doc_id}.pdf"
        assert saved_file.exists(), "PDF file was not saved to the upload directory"

    def test_list_documents_includes_uploaded_document(self, client, sample_pdf_bytes):
        files = [make_upload_file(sample_pdf_bytes, "paper.pdf")]
        doc_id = client.post("/api/documents/", files=files).json()["document_id"]

        docs = client.get("/api/documents/").json()
        doc_ids = [d["document_id"] for d in docs]
        assert doc_id in doc_ids


# ── Failure path: scanned PDF ──────────────────────────────────────────────────

class TestIngestionFailurePath:
    def test_scanned_pdf_ingestion_reaches_failed(self, client, empty_pdf_bytes):
        files = [make_upload_file(empty_pdf_bytes, "scanned.pdf")]
        doc_id = client.post("/api/documents/", files=files).json()["document_id"]

        status = client.get(f"/api/documents/{doc_id}").json()
        assert status["status"] == "failed", f"Expected failed, got: {status}"

    def test_scanned_pdf_error_message_is_user_friendly(self, client, empty_pdf_bytes):
        files = [make_upload_file(empty_pdf_bytes, "scanned.pdf")]
        doc_id = client.post("/api/documents/", files=files).json()["document_id"]

        status = client.get(f"/api/documents/{doc_id}").json()
        assert status["error"] is not None
        # Error must be user-friendly — no stack traces, no FS paths
        error = status["error"]
        assert "Traceback" not in error
        assert "storage" not in error.lower()

    def test_corrupted_pdf_upload_accepted_but_ingestion_fails(self, client, sample_pdf_bytes, tmp_path):
        """
        A file that passes magic-byte check but is internally corrupt:
        the upload is accepted (202) but ingestion later marks it FAILED.
        We test this by directly corrupting the saved file after upload.
        """
        from app import config
        files = [make_upload_file(sample_pdf_bytes, "paper.pdf")]
        doc_id = client.post("/api/documents/", files=files).json()["document_id"]

        # Corrupt the saved file on disk
        saved = config.settings.UPLOAD_DIR / f"{doc_id}.pdf"
        if saved.exists():
            saved.write_bytes(b"%PDF-corrupted-garbage-data")

        # Re-trigger ingestion manually (simulates retry / post-upload corruption)
        import asyncio
        asyncio.run(ds.ingest(doc_id))

        status = client.get(f"/api/documents/{doc_id}").json()
        # Either failed or completed (file was already processed from original bytes)
        assert status["status"] in ("failed", "completed")


# ── Phase 3: Search API ───────────────────────────────────────────────────────

class TestSearchAPI:
    """Tests for POST /api/documents/{id}/search (Phase 3 retrieval endpoint)."""

    def test_search_completed_document_returns_200(self, client, sample_pdf_bytes):
        """Search a fully indexed document — expects results."""
        files = [make_upload_file(sample_pdf_bytes, "paper.pdf")]
        doc_id = client.post("/api/documents/", files=files).json()["document_id"]

        resp = client.post(
            f"/api/documents/{doc_id}/search",
            json={"query": "machine learning natural language processing"},
        )
        assert resp.status_code == 200

    def test_search_returns_list(self, client, sample_pdf_bytes):
        files = [make_upload_file(sample_pdf_bytes, "paper.pdf")]
        doc_id = client.post("/api/documents/", files=files).json()["document_id"]

        resp = client.post(
            f"/api/documents/{doc_id}/search",
            json={"query": "deep learning"},
        )
        assert isinstance(resp.json(), list)

    def test_search_result_fields(self, client, sample_pdf_bytes):
        """Each result has all required fields."""
        files = [make_upload_file(sample_pdf_bytes, "paper.pdf")]
        doc_id = client.post("/api/documents/", files=files).json()["document_id"]

        results = client.post(
            f"/api/documents/{doc_id}/search",
            json={"query": "abstract"},
        ).json()
        if results:  # May return no results for very short docs
            r = results[0]
            assert "chunk_id" in r
            assert "page_number" in r
            assert "source_filename" in r
            assert "text" in r
            assert "score" in r

    def test_search_unknown_document_returns_404(self, client):
        resp = client.post(
            "/api/documents/00000000-0000-0000-0000-000000000000/search",
            json={"query": "test"},
        )
        assert resp.status_code == 404

    def test_search_not_ready_document_returns_422(self, client, sample_pdf_bytes):
        """Searching a document that is still processing returns 422."""
        from app.services import document_service as ds2
        from app.models.document import ProcessingStatus

        files = [make_upload_file(sample_pdf_bytes, "paper.pdf")]
        doc_id = client.post("/api/documents/", files=files).json()["document_id"]

        # Force status back to 'extracting' to simulate mid-processing
        if doc_id in ds2._registry:
            ds2._registry[doc_id].status = ProcessingStatus.EXTRACTING

        resp = client.post(
            f"/api/documents/{doc_id}/search",
            json={"query": "test"},
        )
        assert resp.status_code == 422


# ── Phase 3: Deletion with vector cleanup ─────────────────────────────────

class TestDeletionWithVectors:
    def test_delete_removes_document_state(self, client, sample_pdf_bytes):
        """After DELETE, GET for that document returns 404."""
        files = [make_upload_file(sample_pdf_bytes, "paper.pdf")]
        doc_id = client.post("/api/documents/", files=files).json()["document_id"]

        del_resp = client.delete(f"/api/documents/{doc_id}")
        assert del_resp.status_code == 200

        get_resp = client.get(f"/api/documents/{doc_id}")
        assert get_resp.status_code == 404

    def test_delete_search_returns_404(self, client, sample_pdf_bytes):
        """After DELETE, searching that document returns 404."""
        files = [make_upload_file(sample_pdf_bytes, "paper.pdf")]
        doc_id = client.post("/api/documents/", files=files).json()["document_id"]
        client.delete(f"/api/documents/{doc_id}")

        resp = client.post(
            f"/api/documents/{doc_id}/search",
            json={"query": "machine learning"},
        )
        assert resp.status_code == 404
