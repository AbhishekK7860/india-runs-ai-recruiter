"""Pydantic schema for a ranked candidate result.

Defines the RankedCandidate model produced by the RankingAgent, containing
both scoring dimensions and a human-readable reasoning string.
"""

from pydantic import BaseModel, Field


class RankedCandidate(BaseModel):
    """A candidate with computed ranking scores and LLM-generated reasoning."""

    rank: int = Field(..., ge=1, description="Final rank position (1 = best).")
    candidate_id: str = Field(..., description="Unique candidate identifier.")
    semantic_score: float = Field(
        ..., ge=0.0, le=1.0, description="Semantic similarity score (0–1)."
    )
    behaviour_score: float = Field(
        ..., ge=0.0, le=1.0, description="Normalised behaviour signal score (0–1)."
    )
    reasoning: str = Field(
        ..., description="LLM-generated rationale for this candidate's ranking."
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in the ranking decision (0–1)."
    )
