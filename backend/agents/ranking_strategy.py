"""Ranking strategy interface and implementations."""

from abc import ABC, abstractmethod

from backend.schemas.llm import CriticReview, EvidencePackage


class RankingStrategy(ABC):
    """Abstract base class for calculating final candidate scores."""

    @abstractmethod
    def calculate_score(
        self, evidence: EvidencePackage, critic_review: CriticReview | None = None
    ) -> float:
        """Calculate the final fused score for a candidate.

        Args:
            evidence: The candidate evidence package containing semantic and behavioral scores.
            critic_review: The optional critic review containing the LLM adjusted fit score.

        Returns:
            A final float score used for sorting candidates.
        """
        pass


class WeightedFusionStrategy(RankingStrategy):
    """Fuses semantic, behavioral, and LLM scores using configured weights."""

    def __init__(
        self,
        semantic_weight: float = 0.2,
        behaviour_weight: float = 0.2,
        llm_weight: float = 0.6,
    ) -> None:
        self.semantic_weight = semantic_weight
        self.behaviour_weight = behaviour_weight
        self.llm_weight = llm_weight

    def calculate_score(
        self, evidence: EvidencePackage, critic_review: CriticReview | None = None
    ) -> float:
        """Calculate the weighted final score."""
        semantic = (
            evidence.semantic_match_score * 100.0
        )  # Normalize to 0-100 if semantic is 0-1
        # if FAISS IP score is already raw dot product, it might not be strictly 0-1.
        # Assuming semantic is cosine sim, we clamp it to 0-1.
        semantic_norm = max(0.0, min(semantic, 100.0))

        behaviour = evidence.behaviour_score * 100.0

        llm_score = 0.0
        if critic_review:
            # Penalty for hallucinations
            penalty = 10.0 if critic_review.is_hallucination_detected else 0.0
            llm_score = max(0.0, critic_review.adjusted_fit_score - penalty)

        final_score = (
            (semantic_norm * self.semantic_weight)
            + (behaviour * self.behaviour_weight)
            + (llm_score * self.llm_weight)
        )
        return round(final_score, 4)
