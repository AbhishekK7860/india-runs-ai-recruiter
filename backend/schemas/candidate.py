"""Pydantic schema for candidate profile data.

Defines the CandidateProfile model representing a normalised view of a
candidate's résumé and professional background.
"""

from pydantic import BaseModel, Field

from backend.schemas.behaviour import BehaviourSignal


class CandidateProfile(BaseModel):
    """Normalised candidate profile used across the ranking pipeline."""

    candidate_id: str = Field(..., description="Unique candidate identifier.")
    name: str = Field(..., description="Anonymised candidate name.")
    skills: list[str] = Field(default_factory=list, description="List of skill names.")
    experience_years: float = Field(
        ..., ge=0.0, description="Total years of professional experience."
    )
    current_role: str = Field(..., description="Current job title.")
    projects: list[str] = Field(
        default_factory=list, description="Notable project names or descriptions."
    )
    education: str = Field(..., description="Highest qualification summary string.")
    resume_text: str = Field(
        ..., description="Full concatenated résumé text for embedding."
    )
    behaviour_signals: BehaviourSignal | None = Field(
        default=None, description="Platform engagement signals"
    )
