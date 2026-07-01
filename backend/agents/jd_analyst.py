"""Job Description Analyst Agent."""

from backend.llm.client import LLMClient
from backend.schemas.llm import JobRequirements
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class JDAnalystAgent:
    """Analyzes raw job descriptions into structured requirements."""

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize the agent with an LLM client."""
        self.llm = llm_client
        self.system_prompt = self.llm.get_prompt("jd_analyst")

    def analyze(self, raw_jd_text: str) -> JobRequirements:
        """Extract structured requirements from a raw job description string.

        Args:
            raw_jd_text: The unstructured job description text.

        Returns:
            A structured JobRequirements Pydantic model.
        """
        logger.info(
            "Analyzing raw job description to extract structured requirements..."
        )

        user_prompt = f"Extract the requirements from the following job description:\n\n{raw_jd_text}"

        result = self.llm.generate_structured(
            system_instruction=self.system_prompt,
            user_prompt=user_prompt,
            response_schema=JobRequirements,
        )

        logger.info(
            f"Successfully extracted JD requirements. Required skills: {len(result.required_skills)}"
        )
        return result
