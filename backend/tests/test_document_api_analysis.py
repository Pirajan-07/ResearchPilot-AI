"""
ResearchPilot AI — Tests: Document API Analysis Endpoints (Phase 5)

Covers:
  - GET /api/documents/{id}/summary
  - GET /api/documents/{id}/insights
"""
from __future__ import annotations

import io
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("GEMINI_API_KEY", "test-dummy-key-phase5-no-gemini-calls")

from main import app
from app.services import document_service as ds
from app.schemas.analysis import PaperSummaryResponse, PaperInsightsResponse


@pytest.fixture(autouse=True)
def clear_registry():
    ds._registry.clear()
    yield
    ds._registry.clear()


@pytest.fixture
def client(tmp_path: Path):
    from app import config
    config.settings.UPLOAD_DIR = tmp_path / "uploads"
    config.settings.CHROMA_PERSIST_DIRECTORY = tmp_path / "chroma"
    config.settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    config.settings.CHROMA_PERSIST_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with TestClient(app) as c:
        yield c


def _upload_and_complete(client, sample_pdf_bytes: bytes) -> str:
    files = [("file", ("paper.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf"))]
    resp = client.post("/api/documents/", files=files)
    doc_id = resp.json()["document_id"]
    client.get(f"/api/documents/{doc_id}").json() # poll
    return doc_id


class TestSummaryAPI:
    def test_summary_unknown_document_returns_404(self, client):
        resp = client.get("/api/documents/00000000-0000-0000-0000-000000000000/summary")
        assert resp.status_code == 404

    def test_summary_not_completed_returns_422(self, client, sample_pdf_bytes):
        files = [("file", ("paper.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf"))]
        doc_id = client.post("/api/documents/", files=files).json()["document_id"]
        
        if doc_id in ds._registry:
            from app.models.document import ProcessingStatus
            ds._registry[doc_id].status = ProcessingStatus.EXTRACTING
            
        resp = client.get(f"/api/documents/{doc_id}/summary")
        assert resp.status_code == 422

    def test_summary_success_returns_200(self, client, sample_pdf_bytes):
        doc_id = _upload_and_complete(client, sample_pdf_bytes)
        
        mock_resp = PaperSummaryResponse(
            overview="Test", problem="Test", objectives="Test", methodology="Test",
            dataset="Test", findings="Test", limitations="Test", conclusion="Test", future_direction="Test"
        )
        
        with patch("app.api.documents.analysis_service.generate_summary", return_value=mock_resp):
            resp = client.get(f"/api/documents/{doc_id}/summary")
            
        assert resp.status_code == 200
        assert "overview" in resp.json()


class TestInsightsAPI:
    def test_insights_unknown_document_returns_404(self, client):
        resp = client.get("/api/documents/00000000-0000-0000-0000-000000000000/insights")
        assert resp.status_code == 404

    def test_insights_success_returns_200(self, client, sample_pdf_bytes):
        doc_id = _upload_and_complete(client, sample_pdf_bytes)
        
        mock_resp = PaperInsightsResponse(
            problem="Test", methodology="Test", dataset="Test", contribution="Test",
            findings=["Test"], limitations=["Test"], future_direction="Test"
        )
        
        with patch("app.api.documents.analysis_service.generate_insights", return_value=mock_resp):
            resp = client.get(f"/api/documents/{doc_id}/insights")
            
        assert resp.status_code == 200
        assert "contribution" in resp.json()
