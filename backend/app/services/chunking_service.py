"""
ResearchPilot AI — Chunking Service

Responsible for splitting extracted page text into overlapping chunks using
LangChain's RecursiveCharacterTextSplitter.

Every chunk carries full provenance metadata:
  - document_id
  - page_number (1-indexed, from PyMuPDF)
  - chunk_id   ("{document_id}_chunk_{index:04d}")
  - chunk_index
  - source_filename (original display filename — for citation only)

This service is PURE — no I/O, no external calls.
"""
from __future__ import annotations

from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger

from app.models.document import DocumentChunk, ExtractedPage


def chunk_pages(
    pages: List[ExtractedPage],
    document_id: str,
    source_filename: str,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> List[DocumentChunk]:
    """
    Split a list of extracted pages into overlapping text chunks.

    Args:
        pages:           List of ExtractedPage objects (from parser_service).
        document_id:     Unique document identifier.
        source_filename: Original filename for citation display only.
        chunk_size:      Target character length per chunk (default from settings).
        chunk_overlap:   Overlap in characters between adjacent chunks.

    Returns:
        Ordered list of DocumentChunk objects, each with full provenance metadata.

    Notes:
        - Pages with empty text are skipped (no chunks produced for blank pages).
        - The LangChain splitter may produce chunks smaller than chunk_size near
          page boundaries — this is expected and acceptable.
        - chunk_id format: "{document_id}_chunk_{index:04d}" (zero-padded to 4 digits,
          supports up to 9999 chunks per document — sufficient for MVP).
    """
    # Build LangChain Document objects (one per non-empty page)
    lc_docs: List[Document] = []
    for page in pages:
        if not page.text.strip():
            logger.debug("Skipping blank page {} for document {}", page.page_number, document_id)
            continue
        lc_docs.append(
            Document(
                page_content=page.text,
                metadata={
                    "page_number": page.page_number,
                    "document_id": document_id,
                    "source_filename": source_filename,
                },
            )
        )

    if not lc_docs:
        logger.warning("No non-empty pages to chunk for document {}", document_id)
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        add_start_index=True,   # adds start_index to metadata for debugging
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    raw_chunks = splitter.split_documents(lc_docs)
    logger.debug(
        "Chunker produced {} raw chunks from {} pages for document {}",
        len(raw_chunks),
        len(lc_docs),
        document_id,
    )

    chunks: List[DocumentChunk] = []
    for idx, raw in enumerate(raw_chunks):
        chunk = DocumentChunk(
            chunk_id=f"{document_id}_chunk_{idx:04d}",
            document_id=document_id,
            text=raw.page_content,
            page_number=raw.metadata.get("page_number", 0),
            chunk_index=idx,
            source_filename=source_filename,
        )
        chunks.append(chunk)

    logger.info(
        "Produced {} chunks (size={}, overlap={}) for document {}",
        len(chunks),
        chunk_size,
        chunk_overlap,
        document_id,
    )
    return chunks
