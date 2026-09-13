"""
ResearchPilot AI — API Router Registry
Aggregates all route modules into a single router.
Routers are added incrementally as phases are implemented.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.documents import router as documents_router

api_router = APIRouter()

# Phase 2: Document upload + status
api_router.include_router(documents_router, prefix="/documents", tags=["Documents"])

# Phase 5+6: Q&A, summary, insights
# from app.api.research import router as research_router
# api_router.include_router(research_router, prefix="/documents", tags=["Research"])
