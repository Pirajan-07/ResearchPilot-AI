"""
ResearchPilot AI — Gemini LLM Provider
Implements BaseLLMProvider using Google Gemini via langchain-google-genai.
Model is read from settings.GEMINI_MODEL — never hard-coded.
"""
from __future__ import annotations

from functools import lru_cache

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from loguru import logger

from app.config import settings
from app.providers.base import BaseLLMProvider


class GeminiLLMProvider(BaseLLMProvider):
    """
    LLM provider backed by Google Gemini via langchain-google-genai.
    The GEMINI_API_KEY is passed directly — never exposed to the browser.
    """

    def get_llm(self) -> BaseChatModel:
        logger.debug("Initialising Gemini LLM — model: {}", settings.GEMINI_MODEL)
        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.1,          # Low for factual, consistent research answers
            max_output_tokens=4096,   # Sufficient for detailed answers + summaries + structured insights
            convert_system_message_to_human=False,
        )


@lru_cache(maxsize=1)
def get_gemini_provider() -> GeminiLLMProvider:
    """Singleton accessor — returns the same provider instance across the app."""
    return GeminiLLMProvider()
