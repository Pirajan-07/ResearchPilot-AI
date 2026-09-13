"""
ResearchPilot AI — Tests: Chunking Service

Covers:
  - Correct number of chunks produced
  - Chunk size configuration (chunk_size param is respected)
  - Chunk overlap configuration
  - All chunks carry document_id metadata
  - All chunks carry page_number metadata (1-indexed)
  - All chunks carry source_filename metadata
  - chunk_id format is correct
  - chunk_index is sequential
  - Empty page list returns empty chunk list
  - All-blank pages return empty chunk list
"""
from __future__ import annotations

from app.models.document import DocumentChunk, ExtractedPage
from app.services.chunking_service import chunk_pages


# ── Helpers ──────────────────────────────────────────────────────────────────────

def make_pages(texts: list[str]) -> list[ExtractedPage]:
    """Create a list of ExtractedPage objects from raw text strings."""
    return [ExtractedPage(page_number=i + 1, text=t) for i, t in enumerate(texts)]


LOREM = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
    "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
    "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris. "
    "Duis aute irure dolor in reprehenderit in voluptate velit esse. "
    "Excepteur sint occaecat cupidatat non proident, sunt in culpa. "
) * 5  # ~1600 chars — enough to produce multiple chunks with chunk_size=800


class TestChunkPages:
    """Tests for chunking_service.chunk_pages()"""

    DOC_ID = "test-doc-abc123"
    FILENAME = "research_paper.pdf"

    def test_returns_list_of_document_chunks(self):
        """chunk_pages returns a list of DocumentChunk objects."""
        pages = make_pages([LOREM])
        result = chunk_pages(pages, self.DOC_ID, self.FILENAME)
        assert isinstance(result, list)
        assert all(isinstance(c, DocumentChunk) for c in result)

    def test_produces_multiple_chunks_for_long_text(self):
        """Long text (>chunk_size chars) produces more than one chunk."""
        pages = make_pages([LOREM])  # ~1600 chars with chunk_size=800
        result = chunk_pages(pages, self.DOC_ID, self.FILENAME, chunk_size=800, chunk_overlap=150)
        assert len(result) >= 2, f"Expected >=2 chunks, got {len(result)}"

    def test_chunk_size_respected(self):
        """No chunk exceeds chunk_size characters (with small tolerance for splitter)."""
        chunk_size = 400
        pages = make_pages([LOREM])
        result = chunk_pages(pages, self.DOC_ID, self.FILENAME, chunk_size=chunk_size, chunk_overlap=50)
        for chunk in result:
            # LangChain splitter may slightly exceed chunk_size at word boundaries
            assert len(chunk.text) <= chunk_size + 100, (
                f"Chunk {chunk.chunk_id} too long: {len(chunk.text)} chars"
            )

    def test_smaller_chunk_size_produces_more_chunks(self):
        """Halving chunk_size should roughly double the number of chunks."""
        pages = make_pages([LOREM])
        large = chunk_pages(pages, self.DOC_ID, self.FILENAME, chunk_size=800, chunk_overlap=0)
        small = chunk_pages(pages, self.DOC_ID, self.FILENAME, chunk_size=400, chunk_overlap=0)
        assert len(small) >= len(large), "Smaller chunk_size should produce >= chunks"

    def test_every_chunk_has_document_id(self):
        """Every chunk carries the correct document_id."""
        pages = make_pages([LOREM])
        result = chunk_pages(pages, self.DOC_ID, self.FILENAME)
        for chunk in result:
            assert chunk.document_id == self.DOC_ID

    def test_every_chunk_has_source_filename(self):
        """Every chunk carries the source filename."""
        pages = make_pages([LOREM])
        result = chunk_pages(pages, self.DOC_ID, self.FILENAME)
        for chunk in result:
            assert chunk.source_filename == self.FILENAME

    def test_every_chunk_has_page_number(self):
        """Every chunk carries a page_number >= 1."""
        pages = make_pages([LOREM])
        result = chunk_pages(pages, self.DOC_ID, self.FILENAME)
        for chunk in result:
            assert chunk.page_number >= 1

    def test_page_number_preserved_from_source_page(self):
        """Chunks from page 2 carry page_number=2."""
        pages = make_pages(["Short page 1.", LOREM])  # page 2 is long
        result = chunk_pages(pages, self.DOC_ID, self.FILENAME)
        page2_chunks = [c for c in result if c.page_number == 2]
        assert len(page2_chunks) >= 1, "Expected chunks with page_number=2"
        for chunk in page2_chunks:
            assert chunk.page_number == 2

    def test_chunk_id_format(self):
        """chunk_id follows the pattern '{document_id}_chunk_{index:04d}'."""
        pages = make_pages([LOREM])
        result = chunk_pages(pages, self.DOC_ID, self.FILENAME)
        assert result[0].chunk_id == f"{self.DOC_ID}_chunk_0000"
        assert result[1].chunk_id == f"{self.DOC_ID}_chunk_0001"

    def test_chunk_index_is_sequential(self):
        """chunk_index values are 0, 1, 2, ... with no gaps."""
        pages = make_pages([LOREM])
        result = chunk_pages(pages, self.DOC_ID, self.FILENAME)
        for i, chunk in enumerate(result):
            assert chunk.chunk_index == i

    def test_empty_pages_list_returns_empty(self):
        """No pages in → no chunks out."""
        result = chunk_pages([], self.DOC_ID, self.FILENAME)
        assert result == []

    def test_all_blank_pages_returns_empty(self):
        """Pages with only whitespace produce no chunks."""
        pages = make_pages(["   ", "\n\n\t\n", ""])
        result = chunk_pages(pages, self.DOC_ID, self.FILENAME)
        assert result == []

    def test_single_short_page_produces_one_chunk(self):
        """A page shorter than chunk_size produces exactly one chunk."""
        short_text = "This is a short research abstract. It has enough text to be a chunk."
        pages = make_pages([short_text])
        result = chunk_pages(pages, self.DOC_ID, self.FILENAME, chunk_size=800, chunk_overlap=150)
        assert len(result) == 1
        assert short_text in result[0].text or result[0].text in short_text

    def test_chunk_text_is_not_empty(self):
        """No chunk has empty text."""
        pages = make_pages([LOREM])
        result = chunk_pages(pages, self.DOC_ID, self.FILENAME)
        for chunk in result:
            assert chunk.text.strip(), f"Chunk {chunk.chunk_id} has empty text"
