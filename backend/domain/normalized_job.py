"""Normalized job domain model."""

from pydantic import BaseModel, Field


class NormalizedJob(BaseModel):
    """Internal domain model for a normalized job requirement."""

    job_id: str = Field(..., description="Unique job identifier.")
    canonical_title: str | None = Field(None, description="Normalized job title.")
    canonical_required_skills: list[str] = Field(
        default_factory=list, description="Normalized required skills."
    )
    canonical_preferred_skills: list[str] = Field(
        default_factory=list, description="Normalized preferred skills."
    )
    canonical_industry: str | None = Field(None, description="Normalized industry.")

    min_experience_years: int = Field(..., ge=0)
    seniority_level: str = Field(..., description="Normalized seniority.")

    # Original data
    raw_title: str = Field(..., description="Original job title.")
    raw_required_skills: list[str] = Field(default_factory=list)
    raw_preferred_skills: list[str] = Field(default_factory=list)
    description: str = Field(..., description="Original job description.")
