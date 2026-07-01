"""Explainability module — Phase 2+ implementation.

Generates human-readable explanations for each ranked candidate's position.
Uses the LLM output from RecruiterAgent combined with score data to produce
concise natural-language justifications suitable for HR review.
"""

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class Explainer:
    """Generates natural-language explanations for each candidate's ranking."""

    def explain(self, ranking: list[dict]) -> list[str]:
        """Produce an explanation string for each ranked candidate.

        Args:
            ranking: List of candidate dicts containing rank, scores, and
                LLM assessment fields.

        Returns:
            A list of explanation strings, one per candidate, in the same
            order as the input ranking.

        Raises:
            NotImplementedError: Until Phase 2 is implemented.
        """
        raise NotImplementedError("Implemented in Phase 2")
