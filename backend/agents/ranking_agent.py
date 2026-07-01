"""Ranking Agent module."""

from backend.agents.ranking_strategy import RankingStrategy
from backend.schemas.llm import CriticReview, EvidencePackage
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class RankingAgent:
    """Agent orchestrating the final ranking of candidates."""

    def __init__(self, strategy: RankingStrategy) -> None:
        """Initialize the agent with a ranking strategy."""
        self.strategy = strategy

    def rank(
        self, candidates: list[tuple[EvidencePackage, CriticReview | None]]
    ) -> list[dict]:
        """Rank candidates based on the injected strategy.

        Args:
            candidates: A list of tuples containing EvidencePackages and optionally their CriticReviews.

        Returns:
            A sorted list of dictionaries containing final ranks and merged scores.
        """
        logger.info(f"Ranking {len(candidates)} candidates...")

        scored_candidates = []
        for evidence, critic in candidates:
            final_score = self.strategy.calculate_score(evidence, critic)

            scored_candidates.append(
                {
                    "candidate_id": evidence.candidate_id,
                    "final_score": final_score,
                    "semantic_score": evidence.semantic_match_score,
                    "behaviour_score": evidence.behaviour_score,
                    "llm_fit_score": critic.adjusted_fit_score if critic else None,
                    "hallucination_flag": critic.is_hallucination_detected
                    if critic
                    else False,
                }
            )

        # Sort descending
        scored_candidates.sort(key=lambda x: x["final_score"], reverse=True)

        # Add 1-indexed rank
        for i, cand in enumerate(scored_candidates, 1):
            cand["rank"] = i

        return scored_candidates
