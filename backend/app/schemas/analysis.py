"""
ResearchPilot AI — API Schemas: Analysis

Pydantic models for Paper Summary and Paper Insights structured outputs.
"""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class PaperSummaryResponse(BaseModel):
    """Structured 9-dimension paper summary."""
    overview: str = Field(description="Paper title, authors (if detectable), venue")
    problem: str = Field(description="The core problem the paper addresses")
    objectives: str = Field(description="What the authors set out to achieve")
    methodology: str = Field(description="Methods, algorithms, frameworks used")
    dataset: str = Field(description="Datasets used; experimental setup")
    findings: str = Field(description="Primary results and conclusions")
    limitations: str = Field(description="Acknowledged constraints and weaknesses")
    conclusion: str = Field(description="Authors' concluding statements")
    future_direction: str = Field(description="Suggested next steps by the authors")


class PaperInsightsResponse(BaseModel):
    """Structured 7-dimension paper insights specific to the uploaded paper."""
    problem: str = Field(description="Specific research problem addressed by THIS paper")
    methodology: str = Field(description="Methodology and method tags specific to THIS paper")
    dataset: str = Field(description="Dataset used by THIS paper")
    contribution: str = Field(description="Main contribution of THIS paper")
    findings: List[str] = Field(description="Key findings of THIS paper")
    limitations: List[str] = Field(description="Limitations of THIS paper")
    future_direction: str = Field(description="Future direction suggested by THIS paper's authors")
