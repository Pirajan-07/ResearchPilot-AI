"""
ResearchPilot AI — Tests: Analysis Service (Phase 5)

Tests for Paper Summary and Paper Insights generation.
All Gemini calls are mocked.
"""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("GEMINI_API_KEY", "test-dummy-key-phase5-no-gemini-calls")

from app.models.document import DocumentState, ProcessingStatus
from app.schemas.analysis import PaperInsightsResponse, PaperSummaryResponse
from app.services import analysis_service, document_service
from app.services.analysis_service import (
    AnalysisConfigurationError,
    AnalysisGenerationError,
    generate_insights,
    generate_summary,
)
from app.services.indexing_service import RetrievedChunk

DOC_ID = "11111111-1111-1111-1111-111111111111"

SAMPLE_CHUNKS = [
    RetrievedChunk(
        chunk_id=f"{DOC_ID}_chunk_0000",
        document_id=DOC_ID,
        page_number=1,
        source_filename="test.pdf",
        text="Abstract. This paper proposes a new method.",
        score=1.0,
    ),
    RetrievedChunk(
        chunk_id=f"{DOC_ID}_chunk_0001",
        document_id=DOC_ID,
        page_number=2,
        source_filename="test.pdf",
        text="Methodology. We use a novel algorithm.",
        score=1.0,
    ),
]


def make_mock_llm(return_value: any = None, side_effect: Exception = None) -> MagicMock:
    mock_structured = MagicMock()
    if side_effect:
        mock_structured.invoke.side_effect = side_effect
    else:
        mock_structured.invoke.return_value = return_value
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured
    return mock_llm


@pytest.fixture(autouse=True)
def setup_document_registry():
    document_service._registry.clear()
    state = DocumentState.create_new(DOC_ID, "test.pdf", "/fake/path/test.pdf")
    state.status = ProcessingStatus.COMPLETED
    document_service._registry[DOC_ID] = state
    yield
    document_service._registry.clear()


@pytest.fixture
def chroma_dir(tmp_path: Path) -> Path:
    d = tmp_path / "chroma"
    d.mkdir()
    return d


# ── Tests for generate_summary ────────────────────────────────────────────────

class TestGenerateSummary:
    def test_summary_returns_expected_schema(self, chroma_dir):
        mock_resp = PaperSummaryResponse(
            overview="Test Overview",
            problem="Test Problem",
            objectives="Test Objectives",
            methodology="Test Methodology",
            dataset="Test Dataset",
            findings="Test Findings",
            limitations="Test Limitations",
            conclusion="Test Conclusion",
            future_direction="Test Future",
        )
        llm = make_mock_llm(return_value=mock_resp)

        with patch("app.services.analysis_service.indexing_service.get_all_chunks", return_value=SAMPLE_CHUNKS):
            result = generate_summary(DOC_ID, chroma_dir, llm_override=llm)
        
        assert isinstance(result, PaperSummaryResponse)
        assert result.overview == "Test Overview"
        
        # Verify it was cached
        state = document_service.get_document(DOC_ID)
        assert state.summary is not None
        assert state.summary["overview"] == "Test Overview"

    def test_summary_returns_cached_if_available(self, chroma_dir):
        # Pre-populate cache
        state = document_service.get_document(DOC_ID)
        state.summary = PaperSummaryResponse(
            overview="Cached Overview", problem="", objectives="", methodology="",
            dataset="", findings="", limitations="", conclusion="", future_direction=""
        ).model_dump()
        
        # LLM should not be called
        llm = make_mock_llm(side_effect=Exception("LLM should not be called"))
        
        with patch("app.services.analysis_service.indexing_service.get_all_chunks") as mock_get_chunks:
            result = generate_summary(DOC_ID, chroma_dir, llm_override=llm)
            
        assert result.overview == "Cached Overview"
        mock_get_chunks.assert_not_called()

    def test_summary_raises_value_error_for_unknown_doc(self, chroma_dir):
        with pytest.raises(ValueError, match="not found"):
            generate_summary("unknown-id", chroma_dir)

    def test_summary_raises_generation_error_on_llm_failure(self, chroma_dir):
        llm = make_mock_llm(side_effect=Exception("Internal Server Error"))
        with patch("app.services.analysis_service.indexing_service.get_all_chunks", return_value=SAMPLE_CHUNKS):
            with pytest.raises(AnalysisGenerationError, match="Gemini generation failed"):
                generate_summary(DOC_ID, chroma_dir, llm_override=llm)


# ── Tests for generate_insights ───────────────────────────────────────────────

class TestGenerateInsights:
    def test_insights_returns_expected_schema(self, chroma_dir):
        mock_resp = PaperInsightsResponse(
            problem="Test Problem",
            methodology="Test Methodology",
            dataset="Test Dataset",
            contribution="Test Contribution",
            findings=["Finding 1"],
            limitations=["Limitation 1"],
            future_direction="Test Future",
        )
        llm = make_mock_llm(return_value=mock_resp)

        with patch("app.services.analysis_service.indexing_service.get_all_chunks", return_value=SAMPLE_CHUNKS):
            result = generate_insights(DOC_ID, chroma_dir, llm_override=llm)
        
        assert isinstance(result, PaperInsightsResponse)
        assert result.contribution == "Test Contribution"
        assert "Finding 1" in result.findings
        
        # Verify it was cached
        state = document_service.get_document(DOC_ID)
        assert state.insights is not None
        assert state.insights["contribution"] == "Test Contribution"

    def test_insights_returns_cached_if_available(self, chroma_dir):
        # Pre-populate cache
        state = document_service.get_document(DOC_ID)
        state.insights = PaperInsightsResponse(
            problem="", methodology="", dataset="", contribution="Cached Contribution",
            findings=[], limitations=[], future_direction=""
        ).model_dump()
        
        # LLM should not be called
        llm = make_mock_llm(side_effect=Exception("LLM should not be called"))
        
        with patch("app.services.analysis_service.indexing_service.get_all_chunks") as mock_get_chunks:
            result = generate_insights(DOC_ID, chroma_dir, llm_override=llm)
            
        assert result.contribution == "Cached Contribution"
        mock_get_chunks.assert_not_called()

    def test_insights_raises_generation_error_on_wrong_type(self, chroma_dir):
        # Model returns wrong type
        llm = make_mock_llm(return_value="Not an insights response object")
        with patch("app.services.analysis_service.indexing_service.get_all_chunks", return_value=SAMPLE_CHUNKS):
            with pytest.raises(AnalysisGenerationError, match="unexpected response type"):
                generate_insights(DOC_ID, chroma_dir, llm_override=llm)

    def test_insights_raises_config_error_on_auth_failure(self, chroma_dir):
        llm = make_mock_llm(side_effect=Exception("Invalid API key"))
        with patch("app.services.analysis_service.indexing_service.get_all_chunks", return_value=SAMPLE_CHUNKS):
            with pytest.raises(AnalysisConfigurationError, match="API key is missing or invalid"):
                generate_insights(DOC_ID, chroma_dir, llm_override=llm)
