"""Base model definitions for the India Runs AI Recruiter.

Provides TimestampedModel, a pydantic v2 base class that automatically
stamps records with created_at and updated_at fields. All domain models
that require audit timestamps should inherit from this class.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class TimestampedModel(BaseModel):
    """Pydantic base model that automatically adds created_at / updated_at timestamps.

    Subclasses may override the defaults when deserialising persisted records.
    """

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when this record was created.",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when this record was last updated.",
    )
