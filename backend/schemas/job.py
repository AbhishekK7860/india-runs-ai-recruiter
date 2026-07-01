"""Pydantic schema for job requirement data.

Defines the JobRequirement model used throughout the pipeline to represent
a structured job description parsed from raw input text.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class JobRequirement(BaseModel):
    """Structured representation of a job description."""

    job_id: str = Field(..., description="Unique identifier for the job posting.")
    title: str = Field(..., description="Job title.")
    description: str = Field(..., description="Full job description text.")
    required_skills: list[str] = Field(
        default_factory=list, description="Mandatory skills for the role."
    )
    preferred_skills: list[str] = Field(
        default_factory=list, description="Nice-to-have skills."
    )
    min_experience_years: int = Field(
        ..., ge=0, description="Minimum years of experience required."
    )
    seniority_level: Literal["junior", "mid", "senior", "lead"] = Field(
        ..., description="Seniority level of the role."
    )
    created_at: datetime = Field(..., description="Timestamp when the job was created.")
