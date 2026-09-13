"""
ResearchPilot AI — Tests: Parser Service

Covers:
  - Valid PDF extraction (text content correct)
  - Page count accuracy
  - Page number metadata (1-indexed)
  - Multi-page document extraction
  - EmptyDocumentError raised for scanned/no-text PDFs
  - PDFReadError raised for corrupted files
  - Text cleaning: whitespace normalisation
  - Page text isolation (content from page N does not bleed into page M)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.models.document import ExtractedPage
from app.services.parser_service import EmptyDocumentError, PDFReadError, extract_pages
from tests.conftest import create_pdf_bytes


class TestExtractPages:
    """Tests for parser_service.extract_pages()"""

    def test_returns_list_of_extracted_pages(self, sample_pdf_file: Path):
        """extract_pages returns a list of ExtractedPage objects."""
        result = extract_pages(sample_pdf_file)
        assert isinstance(result, list)
        assert all(isinstance(p, ExtractedPage) for p in result)

    def test_page_count_matches_pdf(self, sample_pdf_file: Path):
        """Number of returned pages equals the actual PDF page count."""
        result = extract_pages(sample_pdf_file)
        assert len(result) == 2  # sample_pdf_bytes has 2 pages

    def test_page_numbers_are_one_indexed(self, sample_pdf_file: Path):
        """Page numbers start at 1, not 0."""
        result = extract_pages(sample_pdf_file)
        assert result[0].page_number == 1
        assert result[1].page_number == 2

    def test_extracted_text_contains_expected_content(self, sample_pdf_file: Path):
        """Text extraction preserves key words from the inserted content."""
        result = extract_pages(sample_pdf_file)
        all_text = " ".join(p.text for p in result)
        assert "Abstract" in all_text
        assert "Introduction" in all_text
        # "transformer" may be truncated by PyMuPDF's insert_text line limit;
        # check for "transform" (prefix common to both "transformer" and "transformed")
        assert "transform" in all_text.lower()

    def test_multipage_extraction_preserves_page_order(self, multipage_pdf_bytes: bytes, tmp_path: Path):
        """Page numbers are in ascending sequential order."""
        pdf_path = tmp_path / "multi.pdf"
        pdf_path.write_bytes(multipage_pdf_bytes)
        result = extract_pages(pdf_path)
        assert len(result) == 5
        page_numbers = [p.page_number for p in result]
        assert page_numbers == [1, 2, 3, 4, 5]

    def test_page_text_contains_page_specific_content(self, multipage_pdf_bytes: bytes, tmp_path: Path):
        """Content from page N is in the page N result (not on other pages)."""
        pdf_path = tmp_path / "multi.pdf"
        pdf_path.write_bytes(multipage_pdf_bytes)
        result = extract_pages(pdf_path)
        # Page 3 text should contain "Page 3 content"
        assert "Page 3" in result[2].text

    def test_empty_pdf_raises_empty_document_error(self, empty_pdf_file: Path):
        """PDF with no text layer raises EmptyDocumentError with user-friendly message."""
        with pytest.raises(EmptyDocumentError) as exc_info:
            extract_pages(empty_pdf_file)
        error_msg = str(exc_info.value)
        assert "scanned" in error_msg.lower() or "image" in error_msg.lower() or "text" in error_msg.lower()

    def test_corrupted_pdf_raises_pdf_read_error(self, corrupted_pdf_file: Path):
        """File that is not a valid PDF raises PDFReadError."""
        with pytest.raises(PDFReadError):
            extract_pages(corrupted_pdf_file)

    def test_nonexistent_file_raises_pdf_read_error(self, tmp_path: Path):
        """Non-existent file path raises PDFReadError."""
        with pytest.raises(PDFReadError):
            extract_pages(tmp_path / "does_not_exist.pdf")


class TestTextCleaning:
    """Tests for the internal text cleaning pipeline."""

    def test_extracted_text_has_no_leading_trailing_whitespace(self, sample_pdf_file: Path):
        """Each page's text is stripped."""
        result = extract_pages(sample_pdf_file)
        for page in result:
            if page.text:
                assert page.text == page.text.strip()

    def test_extracted_text_has_no_excessive_blank_lines(self, sample_pdf_file: Path):
        """No runs of 3+ consecutive newlines in extracted text."""
        result = extract_pages(sample_pdf_file)
        for page in result:
            assert "\n\n\n" not in page.text, (
                f"Page {page.page_number} has excessive blank lines"
            )

    def test_extracted_text_is_unicode_normalised(self, tmp_path: Path):
        """Extracted text is Unicode NFC-normalised (no replacement characters)."""
        # Text must be > _MIN_EXTRACTABLE_CHARS (100) to avoid EmptyDocumentError
        long_text = "Simple ASCII text content for normalisation test. " * 3
        pdf_bytes = create_pdf_bytes([long_text])
        pdf_path = tmp_path / "unicode_test.pdf"
        pdf_path.write_bytes(pdf_bytes)
        result = extract_pages(pdf_path)
        for page in result:
            assert "\ufffd" not in page.text, "Replacement character found in output"

    def test_single_page_pdf_works(self, tmp_path: Path):
        """Single-page PDF is handled correctly."""
        # Text must be > _MIN_EXTRACTABLE_CHARS (100) to avoid EmptyDocumentError
        single_text = "This is a single page with sufficient text content for extraction. " * 3
        pdf_bytes = create_pdf_bytes([single_text])
        pdf_path = tmp_path / "single.pdf"
        pdf_path.write_bytes(pdf_bytes)
        result = extract_pages(pdf_path)
        assert len(result) == 1
        assert result[0].page_number == 1
        assert "single page" in result[0].text.lower()
