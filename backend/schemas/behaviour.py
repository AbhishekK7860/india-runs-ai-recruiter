"""Pydantic schema for behavioural signal data.

Defines the BehaviourSignal model which wraps Redrob platform engagement
signals used by the BehaviourAnalystAgent to compute a behaviour score.
"""

from pydantic import BaseModel, Field


class BehaviourSignal(BaseModel):
    """Platform engagement signals sourced from the Redrob ecosystem."""

    candidate_id: str = Field(..., description="Unique candidate identifier.")
    github_activity_score: float = Field(
        default=0.0, description="GitHub activity score (0–100, -1 if not linked)."
    )
    recruiter_response_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Fraction of recruiter messages responded to.",
    )
    profile_completeness: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Profile completeness percentage.",
    )
    notice_period_days: int = Field(
        default=0, ge=0, description="Notice period in days."
    )
    interview_completed: bool = Field(
        default=False,
        description="Whether the candidate has completed at least one interview.",
    )
