"""
ResearchPilot AI — Loguru Logging Configuration
Call setup_logging() once at application startup.
"""
from __future__ import annotations

import sys

from loguru import logger


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure loguru for the application.
    Removes the default handler and adds a structured console handler.
    """
    logger.remove()  # Remove default stderr handler

    logger.add(
        sys.stderr,
        level=log_level.upper(),
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
        backtrace=True,
        diagnose=False,  # Set True in development to show variable values in tracebacks
    )

    # SECURITY: Never log the API key value — confirmed here
    logger.info("Logging initialised at level: {}", log_level.upper())
