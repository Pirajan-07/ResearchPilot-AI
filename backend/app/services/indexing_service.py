"""
ResearchPilot AI — Indexing Service

Responsible for:
  1. Embedding document chunks using LocalHuggingFaceEmbeddingProvider
  2. Persisting embeddings + metadata into ChromaDB
  3. Providing semantic retrieval (used by the Q&A phase)
  4. Cleaning up vectors on document deletion

Design:
  - One ChromaDB collection per document, named: doc_{uuid_no_hyphens}
  - The same embedding function is used for both indexing AND querying
    (guaranteed by using get_embedding_provider() singleton)
  - ChromaDB is the persistent source of truth for chunk vectors
  - DocumentChunk metadata is fully preserved in ChromaDB metadata fields

SECURITY:
  - Gemini is NOT called here.
  - GEMINI_API_KEY is not accessed.
  - No external API calls.
  - ChromaDB paths are never exposed to the client.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import chromadb
from langchain_chroma import Chroma
from loguru import logger

from app.models.document import DocumentChunk
from app.providers.huggingface_provider import get_embedding_provider


# ── Collection naming ───────────────────────────────────────────────────────────

def _collection_name(document_id: str) -> str:
    """
    Derive a safe ChromaDB collection name from a document UUID.

    ChromaDB collection name rules:
      - 3–512 characters
      - Start and end with an alphanumeric character
      - Only alphanumeric, underscores, hyphens

    Format: "doc_" + UUID4 with hyphens removed = 4 + 32 = 36 chars. Always valid.
    """
    return f"doc_{document_id.replace('-', '')}"


# ── Return types ────────────────────────────────────────────────────────────────

@dataclass
class IndexingResult:
    """Summary returned after a successful indexing run."""
    document_id: str
    collection_name: str
    chunks_indexed: int


@dataclass
class RetrievedChunk:
    """A single result from a similarity search."""
    chunk_id: str
    document_id: str
    page_number: int
    source_filename: str
    text: str
    score: float        # Relevance score (higher is better, range varies by metric)


# ── Custom exceptions ───────────────────────────────────────────────────────────

class IndexingError(Exception):
    """Raised when ChromaDB indexing fails."""
    pass


class RetrievalError(Exception):
    """Raised when ChromaDB retrieval fails."""
    pass


# ── Internal helpers ────────────────────────────────────────────────────────────

def _get_vectorstore(document_id: str, chroma_dir: Path) -> Chroma:
    """
    Get a LangChain Chroma vectorstore for the given document's collection.
    Uses the process-level cached embedding function.

    Collection is configured with cosine distance (hnsw:space=cosine) which is
    the correct metric for L2-normalized vectors (our embedding config sets
    normalize_embeddings=True). This prevents relevance score out-of-range warnings.
    """
    embedding_fn = get_embedding_provider().get_embeddings()
    return Chroma(
        collection_name=_collection_name(document_id),
        embedding_function=embedding_fn,
        persist_directory=str(chroma_dir),
        collection_metadata={"hnsw:space": "cosine"},
    )


# ── Public API ──────────────────────────────────────────────────────────────────

def index_document(
    document_id: str,
    chunks: List[DocumentChunk],
    chroma_dir: Path,
) -> IndexingResult:
    """
    Embed all chunks and persist them in ChromaDB.

    Each chunk is stored with its full provenance metadata:
      document_id, chunk_id, page_number, source_filename, chunk_index

    Duplicate handling:
      - Chunks are identified by chunk_id (used as the ChromaDB document ID).
      - Re-indexing the same chunk_id updates the existing entry (ChromaDB upsert).
      - This prevents stale vectors from a partial previous indexing run.

    Args:
        document_id: UUID of the document being indexed.
        chunks:      List of DocumentChunk objects from the chunking phase.
        chroma_dir:  Path to the ChromaDB persistence directory.

    Returns:
        IndexingResult with count of chunks indexed.

    Raises:
        IndexingError: On any ChromaDB or embedding failure.
    """
    if not chunks:
        logger.warning("index_document called with no chunks for document_id={}", document_id)
        return IndexingResult(
            document_id=document_id,
            collection_name=_collection_name(document_id),
            chunks_indexed=0,
        )

    col_name = _collection_name(document_id)
    logger.info(
        "Indexing {} chunks into collection '{}' at {}",
        len(chunks),
        col_name,
        chroma_dir,
    )

    try:
        vectorstore = _get_vectorstore(document_id, chroma_dir)

        texts = [c.text for c in chunks]
        metadatas = [
            {
                "document_id": c.document_id,
                "chunk_id": c.chunk_id,
                "page_number": c.page_number,
                "source_filename": c.source_filename,
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ]
        ids = [c.chunk_id for c in chunks]

        # add_texts with explicit IDs performs upsert — safe for re-indexing
        vectorstore.add_texts(texts=texts, metadatas=metadatas, ids=ids)

    except Exception as exc:
        logger.error(
            "ChromaDB indexing failed for document_id={}: {}",
            document_id,
            exc,
        )
        # Attempt cleanup to avoid leaving partial vectors
        try:
            delete_document_vectors(document_id, chroma_dir)
        except Exception as cleanup_exc:
            logger.warning("Cleanup after indexing failure also failed: {}", cleanup_exc)
        raise IndexingError(f"Failed to index document into vector store: {exc}") from exc

    result = IndexingResult(
        document_id=document_id,
        collection_name=col_name,
        chunks_indexed=len(chunks),
    )
    logger.info(
        "Indexing complete: {} chunks in collection '{}' for document_id={}",
        result.chunks_indexed,
        col_name,
        document_id,
    )
    return result


def delete_document_vectors(document_id: str, chroma_dir: Path) -> None:
    """
    Delete all ChromaDB vectors for a document by dropping its collection.

    Safe to call even if the collection does not exist (e.g. deletion after
    a failed indexing run).

    Args:
        document_id: UUID of the document whose vectors should be deleted.
        chroma_dir:  Path to the ChromaDB persistence directory.
    """
    col_name = _collection_name(document_id)
    logger.info(
        "Deleting ChromaDB collection '{}' for document_id={}",
        col_name,
        document_id,
    )
    try:
        client = chromadb.PersistentClient(path=str(chroma_dir))
        existing = [c.name for c in client.list_collections()]
        if col_name in existing:
            client.delete_collection(col_name)
            logger.info("Deleted collection '{}' successfully.", col_name)
        else:
            logger.debug(
                "Collection '{}' does not exist — nothing to delete.", col_name
            )
    except Exception as exc:
        # Log but do not re-raise — deletion is best-effort during cleanup
        logger.error(
            "Failed to delete ChromaDB collection '{}': {}", col_name, exc
        )


def search_document(
    document_id: str,
    query: str,
    chroma_dir: Path,
    top_k: int = 5,
) -> List[RetrievedChunk]:
    """
    Perform semantic similarity search within a single document's vector collection.

    Uses the SAME embedding provider as indexing — guaranteeing query vectors
    are in the same embedding space as stored document vectors.

    Args:
        document_id: UUID of the document to search within.
        query:       Natural language query string.
        chroma_dir:  Path to the ChromaDB persistence directory.
        top_k:       Maximum number of chunks to return (default: 5).

    Returns:
        List of RetrievedChunk objects ordered by relevance (most relevant first).
        Returns an empty list if the document has no indexed vectors.

    Raises:
        RetrievalError: On ChromaDB or embedding failure.
    """
    col_name = _collection_name(document_id)
    logger.debug(
        "Searching collection '{}' for query (top_k={}): {}...",
        col_name,
        top_k,
        query[:80],
    )

    try:
        # Check the collection exists before attempting search
        client = chromadb.PersistentClient(path=str(chroma_dir))
        existing = [c.name for c in client.list_collections()]
        if col_name not in existing:
            logger.warning(
                "Collection '{}' not found for document_id={} — returning empty results.",
                col_name,
                document_id,
            )
            return []

        vectorstore = _get_vectorstore(document_id, chroma_dir)
        # Use similarity_search_with_score which returns raw cosine distances.
        # With hnsw:space=cosine, distance ∈ [0, 2].
        # Convert to similarity: score = max(0.0, 1.0 - distance)
        raw_results = vectorstore.similarity_search_with_score(query, k=top_k)

    except Exception as exc:
        logger.error(
            "ChromaDB retrieval failed for document_id={}: {}", document_id, exc
        )
        raise RetrievalError(f"Failed to search vector store: {exc}") from exc

    results: List[RetrievedChunk] = []
    for doc, distance in raw_results:
        meta = doc.metadata
        # Convert cosine distance → similarity score ∈ [0, 1]
        similarity = max(0.0, 1.0 - distance)
        results.append(
            RetrievedChunk(
                chunk_id=meta.get("chunk_id", ""),
                document_id=meta.get("document_id", document_id),
                page_number=meta.get("page_number", 0),
                source_filename=meta.get("source_filename", ""),
                text=doc.page_content,
                score=similarity,
            )
        )

    logger.debug(
        "Retrieval returned {} results for document_id={}",
        len(results),
        document_id,
    )
    return results


def get_all_chunks(
    document_id: str,
    chroma_dir: Path,
) -> List[RetrievedChunk]:
    """
    Retrieve all chunks for a document from the vector store.
    
    Used when the full document context is needed (e.g. generating full summaries)
    rather than a top-k semantic search.

    Args:
        document_id: UUID of the document.
        chroma_dir: Path to the ChromaDB persistence directory.
        
    Returns:
        List of RetrievedChunk objects ordered by chunk_index.
        Returns an empty list if the collection is not found.
    """
    col_name = _collection_name(document_id)
    
    try:
        client = chromadb.PersistentClient(path=str(chroma_dir))
        existing = [c.name for c in client.list_collections()]
        if col_name not in existing:
            return []

        vectorstore = _get_vectorstore(document_id, chroma_dir)
        raw_data = vectorstore.get()
        
        results: List[RetrievedChunk] = []
        
        # vectorstore.get() returns dict with keys: 'ids', 'embeddings', 'metadatas', 'documents'
        ids = raw_data.get("ids", [])
        documents = raw_data.get("documents", [])
        metadatas = raw_data.get("metadatas", [])
        
        for i in range(len(ids)):
            meta = metadatas[i] if metadatas and metadatas[i] else {}
            results.append(
                RetrievedChunk(
                    chunk_id=ids[i],
                    document_id=meta.get("document_id", document_id),
                    page_number=meta.get("page_number", 0),
                    source_filename=meta.get("source_filename", ""),
                    text=documents[i],
                    score=1.0, # Not a search, so score is 1.0
                )
            )
            
        # Sort by chunk_index to preserve document order
        results.sort(key=lambda r: int(r.chunk_id.split('_')[-1]) if '_' in r.chunk_id else 0)
        return results

    except Exception as exc:
        logger.error(
            "Failed to retrieve all chunks for document_id={}: {}", document_id, exc
        )
        raise RetrievalError(f"Failed to retrieve all chunks: {exc}") from exc
