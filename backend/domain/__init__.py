"""Domain models package."""

from backend.domain.normalized_candidate import NormalizedCandidate, QualityScoreDetails
from backend.domain.normalized_job import NormalizedJob

__all__ = [
    "NormalizedCandidate",
    "NormalizedJob",
    "QualityScoreDetails",
]
