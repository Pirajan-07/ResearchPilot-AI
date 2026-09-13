"""
ResearchPilot AI — Parser Service

Responsible for:
  1. Opening a PDF file safely with PyMuPDF (fitz)
  2. Extracting text page-by-page (preserving page number metadata)
  3. Cleaning the raw extracted text (whitespace normalisation, Unicode)
  4. Detecting empty / image-only PDFs and raising a user-friendly error

This service is PURE — no I/O side effects other than reading the PDF file.
It does NOT call Gemini, ChromaDB, or any external service.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import List

import fitz  # PyMuPDF
from loguru import logger

from app.models.document import ExtractedPage

# Minimum characters across the whole document to be considered "text-extractable".
# Research papers are typically tens of thousands of characters.
_MIN_EXTRACTABLE_CHARS = 100


# ── Custom Exceptions ───────────────────────────────────────────────────────────

class PDFReadError(Exception):
    """Raised when PyMuPDF cannot open or read the PDF."""
    pass


class EmptyDocumentError(Exception):
    """
    Raised when the PDF contains no extractable text.
    This covers:
      - Purely image-based / scanned PDFs
      - PDFs with only vector graphics (no text layer)
      - Password-protected PDFs whose content cannot be decoded
    """
    pass


# ── Internal helpers ────────────────────────────────────────────────────────────

def _clean_text(raw: str) -> str:
    """
    Apply safe, conservative text cleaning to raw PyMuPDF output.

    Rules:
    - Normalize Unicode to NFC (canonical composed form) for consistent encoding.
    - Replace Unicode replacement character (U+FFFD) — artefact of bad encoding.
    - Collapse runs of more than 2 consecutive newlines into 2 (preserve paragraph breaks).
    - Collapse runs of horizontal whitespace (spaces/tabs) within a line to a single space.
    - Strip leading/trailing whitespace from each line.
    - Strip leading/trailing whitespace from the full result.

    What we deliberately do NOT do:
    - We do not remove hyphens, dashes, or special math symbols.
    - We do not re-flow or rewrite sentences.
    - We do not remove section headings or reference markers.
    - We do not truncate or summarize.
    """
    # 1. Normalize Unicode to NFC
    text = unicodedata.normalize("NFC", raw)

    # 2. Remove Unicode replacement character (bad encoding artefact)
    text = text.replace("\ufffd", " ")

    # 3. Normalize line endings to \n
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 4. Clean within each line: collapse horizontal whitespace
    lines = text.split("\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in lines]
    text = "\n".join(lines)

    # 5. Collapse runs of 3+ blank lines to 2 blank lines (preserve paragraph breaks)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 6. Final strip
    return text.strip()


# ── Public API ──────────────────────────────────────────────────────────────────

def extract_pages(file_path: Path) -> List[ExtractedPage]:
    """
    Open a PDF and extract text page-by-page.

    Args:
        file_path: Absolute path to the PDF file on disk.

    Returns:
        List of ExtractedPage objects, one per page that has extractable text.
        Pages with no text are included (with empty .text) so page count is accurate.

    Raises:
        PDFReadError: If the file cannot be opened or read by PyMuPDF.
        EmptyDocumentError: If the PDF contains no extractable text at all
            (e.g. scanned/image-only PDF).
    """
    logger.debug("Opening PDF for extraction: {}", file_path)

    try:
        doc = fitz.open(str(file_path))
    except fitz.FileDataError as exc:
        raise PDFReadError(f"File appears to be corrupted or is not a valid PDF: {exc}") from exc
    except Exception as exc:
        raise PDFReadError(f"Failed to open PDF: {exc}") from exc

    pages: List[ExtractedPage] = []
    total_chars = 0

    try:
        num_pages = len(doc)
        logger.debug("PDF has {} page(s)", num_pages)

        for i in range(num_pages):
            page = doc.load_page(i)
            raw_text = page.get_text("text")  # type: ignore[arg-type]
            cleaned = _clean_text(raw_text)
            total_chars += len(cleaned)
            pages.append(ExtractedPage(page_number=i + 1, text=cleaned))

    finally:
        doc.close()

    if total_chars < _MIN_EXTRACTABLE_CHARS:
        logger.warning(
            "PDF '{}' yielded only {} chars total — treating as empty/scanned.",
            file_path.name,
            total_chars,
        )
        raise EmptyDocumentError(
            "This PDF does not contain extractable text. "
            "It may be a scanned or image-only document. "
            "The ResearchPilot AI MVP supports text-based PDFs only — "
            "OCR is not available in the current version."
        )

    logger.info(
        "Extracted {} page(s), {} total chars from '{}'",
        len(pages),
        total_chars,
        file_path.name,
    )
    return pages
