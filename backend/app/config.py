"""
ResearchPilot AI — Application Configuration
Reads all settings from environment variables via pydantic-settings.
The .env file is loaded automatically by pydantic-settings.
"""
from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralised configuration for the ResearchPilot AI backend.
    All values are read from environment variables (or .env file).
    No secrets are hard-coded here.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # === AI Providers ===
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-3.5-flash"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # === Storage ===
    UPLOAD_DIR: Path = Path("./storage/uploads")
    CHROMA_PERSIST_DIRECTORY: Path = Path("./storage/chroma_db")

    # === Processing Parameters ===
    MAX_UPLOAD_SIZE_MB: int = 50
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    RETRIEVAL_TOP_K: int = 5

    # === Server ===
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # === CORS ===
    # Accepts a JSON array or a comma-separated string in .env
    # Example: CORS_ORIGINS=http://localhost:3000,http://localhost:3001
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS from comma-separated string into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @field_validator("GEMINI_API_KEY")
    @classmethod
    def gemini_api_key_must_not_be_empty(cls, v: str) -> str:
        if not v or v.strip() == "" or v == "your_gemini_api_key_here":
            raise ValueError(
                "\n\n"
                "  ❌  GEMINI_API_KEY is not set.\n"
                "  Create backend/.env and set: GEMINI_API_KEY=your_key_here\n"
                "  Get a key at: https://aistudio.google.com/apikey\n"
            )
        return v.strip()

    @field_validator("CHUNK_SIZE")
    @classmethod
    def chunk_size_must_be_positive(cls, v: int) -> int:
        if v < 100:
            raise ValueError("CHUNK_SIZE must be at least 100 characters.")
        if v > 2000:
            raise ValueError(
                "CHUNK_SIZE > 2000 risks exceeding the embedding model token limit "
                "(all-MiniLM-L6-v2 max: 256 tokens ≈ 1024 chars)."
            )
        return v

    @field_validator("RETRIEVAL_TOP_K")
    @classmethod
    def top_k_must_be_in_range(cls, v: int) -> int:
        if not (1 <= v <= 20):
            raise ValueError("RETRIEVAL_TOP_K must be between 1 and 20.")
        return v

    @model_validator(mode="after")
    def ensure_storage_directories_exist(self) -> "Settings":
        """Create storage directories if they don't exist."""
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.CHROMA_PERSIST_DIRECTORY.mkdir(parents=True, exist_ok=True)
        return self

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


# Singleton — import this throughout the app
settings = Settings()
