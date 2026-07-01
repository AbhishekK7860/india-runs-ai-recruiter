"""Recruiter Agent module."""


from backend.llm.client import LLMClient
from backend.schemas.llm import EvidencePackage, JobRequirements, RecruiterEvaluation
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class RecruiterAgent:
    """LLM agent responsible for evaluating candidates against job requirements."""

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize the agent with an LLM client."""
        self.llm = llm_client
        self.system_prompt = self.llm.get_prompt("recruiter")

    def evaluate(
        self, evidence: EvidencePackage, job_reqs: JobRequirements
    ) -> RecruiterEvaluation:
        """Evaluate a single candidate's evidence against the structured job requirements.

        Args:
            evidence: The compact structured candidate data.
            job_reqs: The structured requirements of the role.

        Returns:
            A RecruiterEvaluation model containing the score and reasoning.
        """
        user_prompt = (
            f"Job Requirements:\n{job_reqs.model_dump_json(indent=2)}\n\n"
            f"Candidate Evidence:\n{evidence.model_dump_json(indent=2)}\n\n"
            "Evaluate the candidate's fit for the role."
        )

        result = self.llm.generate_structured(
            system_instruction=self.system_prompt,
            user_prompt=user_prompt,
            response_schema=RecruiterEvaluation,
        )

        # Ensure ID matches the input evidence
        result.candidate_id = evidence.candidate_id

        return result
