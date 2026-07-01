"""Normalized candidate domain model."""

from pydantic import BaseModel, Field


class QualityScoreDetails(BaseModel):
    """Breakdown of the candidate's deterministic data quality score."""

    missing_summary: bool = False
    missing_education: bool = False
    invalid_github: bool = False
    empty_skills: bool = False
    inconsistent_experience: bool = False
    total_penalty: float = 0.0


class NormalizedCandidate(BaseModel):
    """Internal domain model for a normalized candidate."""

    candidate_id: str = Field(..., description="Unique candidate identifier.")
    canonical_title: str | None = Field(None, description="Normalized job title.")
    canonical_skills: list[str] = Field(
        default_factory=list, description="Normalized skill names."
    )
    canonical_industry: str | None = Field(None, description="Normalized industry.")
    experience_years: float = Field(..., ge=0.0)

    quality_score: float = Field(
        ..., ge=0.0, le=1.0, description="Deterministic data quality score (0-1)."
    )
    quality_details: QualityScoreDetails = Field(
        default_factory=QualityScoreDetails, description="Reasons for quality score."
    )

    # Original data retained for reference
    raw_title: str = Field(..., description="Original job title.")
    raw_skills: list[str] = Field(default_factory=list, description="Original skills.")
    resume_text: str = Field(..., description="Full text for embeddings.")
