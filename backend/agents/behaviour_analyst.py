"""Behaviour Analyst Agent."""

from backend.schemas.candidate import CandidateProfile
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class BehaviourAnalystAgent:
    """Analyzes candidate platform behavior into a deterministic score."""

    def analyze(self, profile: CandidateProfile) -> float:
        """Calculate a composite behavior score (0-1) from profile completeness and engagement.

        Args:
            profile: The raw CandidateProfile schema containing engagement signals.

        Returns:
            A float score between 0.0 and 1.0.
        """
        score = 0.0

        # 1. Profile Completeness (max 0.6)
        # We check presence of basic fields
        completeness_points = 0
        if profile.name:
            completeness_points += 1
        if profile.current_role:
            completeness_points += 1
        if profile.skills:
            completeness_points += 1
        if profile.experience_years and profile.experience_years > 0:
            completeness_points += 1
        if profile.education:
            completeness_points += 1

        score += (completeness_points / 5.0) * 0.6

        # 2. Project/Portfolio Engagement (max 0.4)
        if profile.projects and len(profile.projects) > 0:
            # Having 1 project is good, having 3+ gives max engagement points
            project_factor = min(len(profile.projects) / 3.0, 1.0)
            score += project_factor * 0.4

        return round(score, 4)
