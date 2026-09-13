"""
ResearchPilot AI — Test Fixtures (conftest.py)

Shared fixtures for all Phase 2 tests.

Key helpers:
  - create_pdf_bytes()  : generate a valid, text-extractable PDF in memory
  - create_empty_pdf()  : generate a PDF with no text layer (simulates scanned PDF)
  - corrupted_pdf_bytes : raw bytes that are NOT a valid PDF
  - test_upload_dir     : temp directory that is isolated per-test
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import fitz  # PyMuPDF
import pytest


# ── PDF creation helpers ────────────────────────────────────────────────────────

def create_pdf_bytes(pages: list[str]) -> bytes:
    """
    Create a minimal but real PDF in memory with actual text content.
    Uses PyMuPDF so the resulting PDF is legitimate and text-extractable.

    Args:
        pages: List of text strings, one per page.

    Returns:
        Raw PDF bytes.
    """
    doc = fitz.open()
    for text in pages:
        page = doc.new_page(width=595, height=842)  # A4
        # Insert at (50, 72) — top-left with margin
        page.insert_text((50, 72), text, fontsize=11, fontname="helv")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_empty_pdf_bytes() -> bytes:
    """
    Create a PDF with no text layer (simulates an image-only / scanned PDF).
    PyMuPDF will open it fine but get_text() returns nothing useful.
    """
    doc = fitz.open()
    doc.new_page()   # Blank page — no text inserted
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


CORRUPTED_PDF_BYTES = b"This is not a PDF file at all."
OVERSIZED_SENTINEL = b"%PDF-fake-oversized"  # For mocking size checks


# ── Fixtures ────────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """A real, two-page, text-extractable PDF."""
    return create_pdf_bytes([
        "Abstract\n\nThis paper presents a novel method for machine learning "
        "applied to natural language processing tasks. We demonstrate state-of-the-art "
        "results on several benchmarks. Our approach relies on transformer architectures.",
        "Introduction\n\nDeep learning has transformed natural language processing. "
        "In this section, we describe the background and motivation for our work. "
        "The contributions of this paper are summarized as follows: (1) a new model, "
        "(2) benchmark results, (3) ablation studies.",
    ])


@pytest.fixture
def multipage_pdf_bytes() -> bytes:
    """A five-page PDF for testing page number metadata preservation."""
    return create_pdf_bytes([
        f"Page {i} content. " + ("Lorem ipsum dolor sit amet. " * 10)
        for i in range(1, 6)
    ])


@pytest.fixture
def empty_pdf_bytes() -> bytes:
    """PDF with no text layer — simulates scanned/image-only document."""
    return create_empty_pdf_bytes()


@pytest.fixture
def corrupted_pdf_bytes() -> bytes:
    """Not a valid PDF at all."""
    return CORRUPTED_PDF_BYTES


@pytest.fixture
def temp_upload_dir(tmp_path: Path) -> Path:
    """Isolated temporary upload directory — cleaned up automatically by pytest."""
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    return upload_dir


@pytest.fixture
def sample_pdf_file(tmp_path: Path, sample_pdf_bytes: bytes) -> Path:
    """Write sample PDF bytes to a temporary file and return its Path."""
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(sample_pdf_bytes)
    return pdf_path


@pytest.fixture
def empty_pdf_file(tmp_path: Path, empty_pdf_bytes: bytes) -> Path:
    """Write empty (no-text) PDF bytes to a temp file."""
    pdf_path = tmp_path / "empty.pdf"
    pdf_path.write_bytes(empty_pdf_bytes)
    return pdf_path


@pytest.fixture
def corrupted_pdf_file(tmp_path: Path, corrupted_pdf_bytes: bytes) -> Path:
    """Write corrupted bytes to a temp file."""
    pdf_path = tmp_path / "corrupted.pdf"
    pdf_path.write_bytes(corrupted_pdf_bytes)
    return pdf_path
