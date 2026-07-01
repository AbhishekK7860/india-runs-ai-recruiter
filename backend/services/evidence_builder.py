"""Evidence builder service.

Converts normalized candidates and retrieval metadata into a compact,
structured JSON payload to optimize LLM reasoning and reduce token usage.
"""

from typing import Any

from backend.domain.normalized_candidate import NormalizedCandidate
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class EvidenceBuilder:
    """Builds structured evidence packages for LLM evaluation."""

    def build_package(
        self,
        candidate: NormalizedCandidate,
        semantic_score: float,
        behaviour_score: float,
        safe_resume_text: str,
    ) -> dict[str, Any]:
        """Convert a candidate and metadata into a compact evidence package.

        Args:
            candidate: The normalized candidate domain object.
            semantic_score: The cosine similarity score from FAISS retrieval.
            behaviour_score: The calculated behavioral signal score.
            safe_resume_text: The security-scrubbed resume text.

        Returns:
            A dictionary representing the compact evidence.
        """
        evidence = {
            "candidate_id": candidate.candidate_id,
            "semantic_match_score": round(semantic_score, 4),
            "behaviour_score": round(behaviour_score, 4),
            "canonical_title": candidate.canonical_title or "Unknown",
            "experience_years": candidate.experience_years,
            "canonical_skills": candidate.canonical_skills,
            # We provide the safe resume text for the LLM to read and extract gaps
            "resume_extract": safe_resume_text,
        }

        # We can also add data quality insights to inform the LLM of missing data
        if candidate.quality_score < 0.8:
            evidence["data_quality_warning"] = (
                "Profile has missing or malformed fields."
            )

        return evidence
