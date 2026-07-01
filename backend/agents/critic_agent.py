"""Critic Agent module."""

from backend.llm.client import LLMClient
from backend.schemas.llm import (
    CriticReview,
    EvidencePackage,
    JobRequirements,
    RecruiterEvaluation,
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class CriticAgent:
    """LLM agent responsible for reviewing and refining recruiter evaluations."""

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize the agent with an LLM client."""
        self.llm = llm_client
        self.system_prompt = self.llm.get_prompt("critic")

    def review(
        self,
        evaluation: RecruiterEvaluation,
        evidence: EvidencePackage,
        job_reqs: JobRequirements,
    ) -> CriticReview:
        """Review an initial evaluation for hallucination or bias, adjusting the score if necessary.

        Args:
            evaluation: The initial evaluation from the RecruiterAgent.
            evidence: The candidate evidence package.
            job_reqs: The structured job requirements.

        Returns:
            A CriticReview model containing the adjusted score and reasoning.
        """
        user_prompt = (
            f"Job Requirements:\n{job_reqs.model_dump_json(indent=2)}\n\n"
            f"Candidate Evidence:\n{evidence.model_dump_json(indent=2)}\n\n"
            f"Initial Recruiter Evaluation:\n{evaluation.model_dump_json(indent=2)}\n\n"
            "Review this evaluation. If the recruiter hallucinated skills not in evidence, "
            "penalize the score. Otherwise, maintain the original fit score."
        )

        result = self.llm.generate_structured(
            system_instruction=self.system_prompt,
            user_prompt=user_prompt,
            response_schema=CriticReview,
        )

        # Ensure IDs and original score context is maintained
        result.candidate_id = evidence.candidate_id
        result.original_fit_score = evaluation.fit_score

        return result
