"""Candidate Analyst Agent — Phase 2+ implementation.

Responsible for evaluating individual candidate profiles against the
structured job requirements produced by JDAnalystAgent. Uses an LLM to
produce a per-candidate relevance assessment dict used by RecruiterAgent.
"""

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class CandidateAnalystAgent:
    """Evaluates a single candidate profile against job requirements."""

    def analyze(self, profile: dict) -> dict:
        """Assess a candidate profile and return an evaluation dict.

        Args:
            profile: A dict representation of a CandidateProfile.

        Returns:
            A dict with keys such as skill_match_score, experience_gap,
            and a brief LLM-generated assessment.

        Raises:
            NotImplementedError: Until Phase 2 is implemented.
        """
        raise NotImplementedError("Implemented in Phase 2")
