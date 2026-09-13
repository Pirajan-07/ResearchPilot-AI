"""
ResearchPilot AI — Provider Base Classes (Abstract)
All LLM and embedding providers implement these interfaces.
This enables swapping providers without touching service code.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel


class BaseLLMProvider(ABC):
    """Abstract base for LLM providers."""

    @abstractmethod
    def get_llm(self) -> BaseChatModel:
        """Return a configured LangChain chat model instance."""
        ...


class BaseEmbeddingProvider(ABC):
    """Abstract base for embedding providers."""

    @abstractmethod
    def get_embeddings(self) -> Embeddings:
        """Return a configured LangChain embeddings instance."""
        ...
