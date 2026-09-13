"""
ResearchPilot AI — Local HuggingFace Embedding Provider
Implements BaseEmbeddingProvider using sentence-transformers running on CPU.
Model is read from settings.EMBEDDING_MODEL — never hard-coded.

First run: downloads ~90 MB model to ~/.cache/huggingface/hub/
Subsequent runs: loads from cache — fast.
"""
from __future__ import annotations

from functools import lru_cache

from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from loguru import logger

from app.config import settings
from app.providers.base import BaseEmbeddingProvider


@lru_cache(maxsize=1)
def _load_embeddings(model_name: str) -> HuggingFaceEmbeddings:
    """
    Load the HuggingFace embedding model exactly ONCE per process.
    Cached by model_name so the 90 MB model is not re-loaded between calls.
    This is the single source of truth for embeddings used for both indexing
    and querying — guaranteeing the same vector space.
    """
    logger.info("Loading embedding model: {} (device: cpu)", model_name)
    logger.info(
        "If this is the first run, the model (~90 MB) will download now. "
        "This may take 30-60 seconds on first use."
    )
    emb = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={
            "normalize_embeddings": True,   # Required for cosine similarity
            "batch_size": 32,
        },
    )
    logger.info("Embedding model '{}' loaded successfully.", model_name)
    return emb


class LocalHuggingFaceEmbeddingProvider(BaseEmbeddingProvider):
    """
    Embedding provider using a local sentence-transformers model.
    Runs entirely on CPU — zero API cost, zero network calls after first download.
    """

    def get_embeddings(self) -> Embeddings:
        """Return the cached embedding model instance."""
        return _load_embeddings(settings.EMBEDDING_MODEL)


@lru_cache(maxsize=1)
def get_embedding_provider() -> LocalHuggingFaceEmbeddingProvider:
    """Singleton accessor — use this everywhere that needs embeddings."""
    return LocalHuggingFaceEmbeddingProvider()
