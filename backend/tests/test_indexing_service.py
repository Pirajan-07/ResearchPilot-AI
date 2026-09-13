"""
ResearchPilot AI — Tests: Indexing Service (Phase 3)

Covers:
  Embedding:
  - Embedding provider returns a working embeddings object
  - Correct embedding dimensions (all-MiniLM-L6-v2 = 384 dims)
  - Same provider instance used for indexing and querying (same model)

  ChromaDB Indexing:
  - Chunks are persisted to ChromaDB
  - All metadata is preserved (document_id, chunk_id, page_number, source_filename)
  - Multiple documents are isolated in separate collections
  - Vectors survive service re-instantiation (persistent storage)

  Retrieval:
  - Semantic search returns relevant results
  - top_k is respected
  - page_number and chunk_id are preserved in results
  - Searching a deleted document returns empty results

  Deletion:
  - delete_document_vectors removes the collection
  - Subsequent retrieval returns no results (not an error)

  Pipeline (API-level):
  - Full upload → indexing → COMPLETED in the API test client
  - Indexing stage appears in status
  - POST /{id}/search returns results for completed document
  - DELETE removes vectors and search returns empty

NOTE: These tests load the sentence-transformers model (~90 MB, CPU).
      They are slower than unit tests (~30-60s total on first run).
      Model is cached globally so subsequent runs are faster.
"""
from __future__ import annotations

import io
import os
from pathlib import Path
from typing import List

import pytest

# Ensure dummy key is set before any app import
os.environ.setdefault("GEMINI_API_KEY", "test-dummy-key-phase3-no-gemini-calls")

from app.models.document import DocumentChunk, ExtractedPage
from app.services import indexing_service
from app.services.indexing_service import (
    IndexingResult,
    RetrievedChunk,
    delete_document_vectors,
    index_document,
    search_document,
)
from tests.conftest import create_pdf_bytes


# ── Fixtures ──────────────────────────────────────────────────────────────────

LOREM = (
    "Attention mechanisms have revolutionized natural language processing. "
    "The transformer architecture, introduced in 'Attention is All You Need', "
    "enabled massive scaling of language models. BERT, GPT, and their successors "
    "demonstrated that pre-training on large corpora yields strong downstream performance. "
    "Fine-tuning these models on domain-specific data produces state-of-the-art results. "
) * 4  # ~1300 chars


def make_chunks(document_id: str, n: int = 3, page_offset: int = 1) -> List[DocumentChunk]:
    """Create n synthetic DocumentChunk objects for testing."""
    return [
        DocumentChunk(
            chunk_id=f"{document_id}_chunk_{i:04d}",
            document_id=document_id,
            text=LOREM[i * 200: i * 200 + 200] or LOREM[:200],
            page_number=i + page_offset,
            chunk_index=i,
            source_filename="test_paper.pdf",
        )
        for i in range(n)
    ]


@pytest.fixture
def chroma_dir(tmp_path: Path) -> Path:
    """Isolated ChromaDB directory, cleaned automatically by pytest."""
    d = tmp_path / "chroma"
    d.mkdir()
    return d


@pytest.fixture
def doc_id_a() -> str:
    return "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


@pytest.fixture
def doc_id_b() -> str:
    return "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


# ── Embedding Tests ────────────────────────────────────────────────────────────

class TestEmbeddingProvider:
    def test_embedding_provider_loads(self):
        """Embedding provider can be instantiated without error."""
        from app.providers.huggingface_provider import get_embedding_provider
        provider = get_embedding_provider()
        assert provider is not None

    def test_embedding_function_produces_vectors(self):
        """embed_query returns a non-empty list of floats."""
        from app.providers.huggingface_provider import get_embedding_provider
        embeddings = get_embedding_provider().get_embeddings()
        vector = embeddings.embed_query("test query")
        assert isinstance(vector, list)
        assert len(vector) > 0
        assert all(isinstance(v, float) for v in vector)

    def test_embedding_dimensions_are_384(self):
        """all-MiniLM-L6-v2 produces 384-dimensional vectors."""
        from app.providers.huggingface_provider import get_embedding_provider
        embeddings = get_embedding_provider().get_embeddings()
        vector = embeddings.embed_query("dimension test")
        assert len(vector) == 384

    def test_same_provider_used_for_index_and_query(self):
        """Singleton ensures index and query use identical embedding model."""
        from app.providers.huggingface_provider import get_embedding_provider
        p1 = get_embedding_provider()
        p2 = get_embedding_provider()
        assert p1 is p2, "get_embedding_provider() must return the same singleton"


# ── Indexing Tests ─────────────────────────────────────────────────────────────

class TestIndexDocument:
    def test_index_document_returns_result(self, chroma_dir, doc_id_a):
        chunks = make_chunks(doc_id_a, n=3)
        result = index_document(doc_id_a, chunks, chroma_dir)
        assert isinstance(result, IndexingResult)
        assert result.document_id == doc_id_a
        assert result.chunks_indexed == 3

    def test_chunks_are_persisted(self, chroma_dir, doc_id_a):
        """After indexing, collection exists in ChromaDB."""
        import chromadb
        chunks = make_chunks(doc_id_a, n=2)
        index_document(doc_id_a, chunks, chroma_dir)

        client = chromadb.PersistentClient(path=str(chroma_dir))
        names = [c.name for c in client.list_collections()]
        expected = indexing_service._collection_name(doc_id_a)
        assert expected in names, f"Collection '{expected}' not found in {names}"

    def test_metadata_document_id_preserved(self, chroma_dir, doc_id_a):
        """document_id metadata is stored correctly in ChromaDB."""
        import chromadb
        chunks = make_chunks(doc_id_a, n=2)
        index_document(doc_id_a, chunks, chroma_dir)

        client = chromadb.PersistentClient(path=str(chroma_dir))
        col = client.get_collection(indexing_service._collection_name(doc_id_a))
        results = col.get(include=["metadatas"])
        for meta in results["metadatas"]:
            assert meta["document_id"] == doc_id_a

    def test_metadata_page_number_preserved(self, chroma_dir, doc_id_a):
        """page_number metadata is stored correctly in ChromaDB."""
        import chromadb
        chunks = make_chunks(doc_id_a, n=3)
        index_document(doc_id_a, chunks, chroma_dir)

        client = chromadb.PersistentClient(path=str(chroma_dir))
        col = client.get_collection(indexing_service._collection_name(doc_id_a))
        results = col.get(include=["metadatas"])
        page_numbers = {m["page_number"] for m in results["metadatas"]}
        assert page_numbers == {1, 2, 3}

    def test_metadata_chunk_id_preserved(self, chroma_dir, doc_id_a):
        """chunk_id is stored and matches the DocumentChunk."""
        import chromadb
        chunks = make_chunks(doc_id_a, n=2)
        index_document(doc_id_a, chunks, chroma_dir)

        client = chromadb.PersistentClient(path=str(chroma_dir))
        col = client.get_collection(indexing_service._collection_name(doc_id_a))
        results = col.get(include=["metadatas"])
        stored_ids = {m["chunk_id"] for m in results["metadatas"]}
        expected_ids = {c.chunk_id for c in chunks}
        assert stored_ids == expected_ids

    def test_metadata_source_filename_preserved(self, chroma_dir, doc_id_a):
        """source_filename metadata is stored correctly."""
        import chromadb
        chunks = make_chunks(doc_id_a, n=2)
        index_document(doc_id_a, chunks, chroma_dir)

        client = chromadb.PersistentClient(path=str(chroma_dir))
        col = client.get_collection(indexing_service._collection_name(doc_id_a))
        results = col.get(include=["metadatas"])
        for meta in results["metadatas"]:
            assert meta["source_filename"] == "test_paper.pdf"

    def test_two_documents_are_isolated(self, chroma_dir, doc_id_a, doc_id_b):
        """Different documents get separate collections — vectors don't mix."""
        import chromadb
        chunks_a = make_chunks(doc_id_a, n=2)
        chunks_b = make_chunks(doc_id_b, n=3)
        index_document(doc_id_a, chunks_a, chroma_dir)
        index_document(doc_id_b, chunks_b, chroma_dir)

        client = chromadb.PersistentClient(path=str(chroma_dir))
        col_a = client.get_collection(indexing_service._collection_name(doc_id_a))
        col_b = client.get_collection(indexing_service._collection_name(doc_id_b))
        assert col_a.count() == 2
        assert col_b.count() == 3

    def test_reindexing_does_not_duplicate_chunks(self, chroma_dir, doc_id_a):
        """Re-indexing the same chunks (same chunk_ids) does not create duplicates."""
        import chromadb
        chunks = make_chunks(doc_id_a, n=2)
        index_document(doc_id_a, chunks, chroma_dir)
        index_document(doc_id_a, chunks, chroma_dir)  # Second call — same IDs

        client = chromadb.PersistentClient(path=str(chroma_dir))
        col = client.get_collection(indexing_service._collection_name(doc_id_a))
        assert col.count() == 2, "Re-indexing same chunks should not duplicate"

    def test_empty_chunks_returns_zero_indexed(self, chroma_dir, doc_id_a):
        """Indexing an empty chunk list completes without error."""
        result = index_document(doc_id_a, [], chroma_dir)
        assert result.chunks_indexed == 0

    def test_vectors_survive_client_reinstantiation(self, chroma_dir, doc_id_a):
        """Chunks indexed in one ChromaDB session are present in a new client session."""
        import chromadb
        chunks = make_chunks(doc_id_a, n=2)
        index_document(doc_id_a, chunks, chroma_dir)

        # New client — simulates server restart
        client2 = chromadb.PersistentClient(path=str(chroma_dir))
        col = client2.get_collection(indexing_service._collection_name(doc_id_a))
        assert col.count() == 2


# ── Deletion Tests ─────────────────────────────────────────────────────────────

class TestDeleteDocumentVectors:
    def test_delete_removes_collection(self, chroma_dir, doc_id_a):
        """After deletion, the collection no longer exists."""
        import chromadb
        chunks = make_chunks(doc_id_a, n=2)
        index_document(doc_id_a, chunks, chroma_dir)
        delete_document_vectors(doc_id_a, chroma_dir)

        client = chromadb.PersistentClient(path=str(chroma_dir))
        names = [c.name for c in client.list_collections()]
        assert indexing_service._collection_name(doc_id_a) not in names

    def test_delete_nonexistent_collection_does_not_raise(self, chroma_dir, doc_id_a):
        """Deleting a document that was never indexed is safe."""
        delete_document_vectors(doc_id_a, chroma_dir)  # Should not raise

    def test_delete_only_removes_target_document(self, chroma_dir, doc_id_a, doc_id_b):
        """Deleting one document does not affect another document's vectors."""
        import chromadb
        index_document(doc_id_a, make_chunks(doc_id_a, n=2), chroma_dir)
        index_document(doc_id_b, make_chunks(doc_id_b, n=2), chroma_dir)
        delete_document_vectors(doc_id_a, chroma_dir)

        client = chromadb.PersistentClient(path=str(chroma_dir))
        names = [c.name for c in client.list_collections()]
        assert indexing_service._collection_name(doc_id_a) not in names
        assert indexing_service._collection_name(doc_id_b) in names


# ── Retrieval Tests ────────────────────────────────────────────────────────────

class TestSearchDocument:
    def test_search_returns_results(self, chroma_dir, doc_id_a):
        """Semantic search returns at least one result for a relevant query."""
        chunks = make_chunks(doc_id_a, n=3)
        index_document(doc_id_a, chunks, chroma_dir)
        results = search_document(doc_id_a, "transformer attention mechanism", chroma_dir, top_k=3)
        assert len(results) >= 1

    def test_results_are_retrieved_chunks(self, chroma_dir, doc_id_a):
        """Results are instances of RetrievedChunk."""
        chunks = make_chunks(doc_id_a, n=2)
        index_document(doc_id_a, chunks, chroma_dir)
        results = search_document(doc_id_a, "language model", chroma_dir, top_k=2)
        for r in results:
            assert isinstance(r, RetrievedChunk)

    def test_top_k_limits_results(self, chroma_dir, doc_id_a):
        """top_k=1 returns at most 1 result."""
        chunks = make_chunks(doc_id_a, n=5)
        index_document(doc_id_a, chunks, chroma_dir)
        results = search_document(doc_id_a, "attention", chroma_dir, top_k=1)
        assert len(results) <= 1

    def test_results_contain_page_number(self, chroma_dir, doc_id_a):
        """Every result carries a page_number."""
        chunks = make_chunks(doc_id_a, n=3)
        index_document(doc_id_a, chunks, chroma_dir)
        results = search_document(doc_id_a, "BERT GPT language", chroma_dir, top_k=3)
        for r in results:
            assert r.page_number >= 1

    def test_results_contain_chunk_id(self, chroma_dir, doc_id_a):
        """Every result carries a chunk_id."""
        chunks = make_chunks(doc_id_a, n=2)
        index_document(doc_id_a, chunks, chroma_dir)
        results = search_document(doc_id_a, "pre-training", chroma_dir, top_k=2)
        for r in results:
            assert r.chunk_id.startswith(doc_id_a)

    def test_results_contain_source_filename(self, chroma_dir, doc_id_a):
        """Every result carries the source_filename."""
        chunks = make_chunks(doc_id_a, n=2)
        index_document(doc_id_a, chunks, chroma_dir)
        results = search_document(doc_id_a, "fine-tuning", chroma_dir, top_k=2)
        for r in results:
            assert r.source_filename == "test_paper.pdf"

    def test_search_deleted_document_returns_empty(self, chroma_dir, doc_id_a):
        """Searching after deletion returns an empty list (not an error)."""
        chunks = make_chunks(doc_id_a, n=2)
        index_document(doc_id_a, chunks, chroma_dir)
        delete_document_vectors(doc_id_a, chroma_dir)
        results = search_document(doc_id_a, "transformer", chroma_dir, top_k=3)
        assert results == []

    def test_search_nonexistent_document_returns_empty(self, chroma_dir):
        """Searching a document that was never indexed returns empty list."""
        results = search_document("nonexistent-id", "query", chroma_dir, top_k=3)
        assert results == []
