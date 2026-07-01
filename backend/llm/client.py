"""Shared LLM infrastructure."""

from typing import Type, TypeVar

from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.semantic_foundation.config_loader import load_yaml_config
from backend.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    """Orchestration layer for LLM interactions.
    
    Delegates actual interactions to the configured provider, handling retries,
    prompt loading, and generic orchestration.
    """

    def __init__(self) -> None:
        """Initialize the LLM Client using the configured provider."""
        self._prompts = load_yaml_config("prompts.yaml")

        from backend.core.settings import get_settings
        settings = get_settings()

        provider_name = settings.LLM_PROVIDER.lower()
        if provider_name == "openrouter":
            from backend.llm.providers.openrouter_provider import OpenRouterProvider
            self.provider = OpenRouterProvider()
        elif provider_name == "google":
            from backend.llm.providers.google_provider import GoogleProvider
            self.provider = GoogleProvider()
        elif provider_name == "local":
            from backend.llm.providers.local_provider import LocalProvider
            self.provider = LocalProvider()
        else:
            raise ValueError(f"Unsupported LLM_PROVIDER: {provider_name}")

        # Run health check to fail fast on configuration issues
        health = self.provider.health_check()
        if health.get("status") == "error":
            logger.error(f"LLM Provider {provider_name} failed health check: {health.get('details')}")
            raise RuntimeError(f"Provider health check failed: {health.get('details')}")
        elif health.get("status") == "warning":
            logger.warning(f"LLM Provider warning: {health.get('details')}")
        else:
            logger.info(f"LLM Provider initialized successfully: {health.get('details')}")

    def get_prompt(self, agent_name: str) -> str:
        """Retrieve the system prompt for a specific agent."""
        if agent_name not in self._prompts:
            raise ValueError(f"Prompt for agent '{agent_name}' not found in configs.")
        return self._prompts[agent_name]["system"]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def generate_structured(self, system_instruction: str, user_prompt: str, response_schema: Type[T]) -> T:
        """Generate a structured response matching a Pydantic schema via the selected provider.

        Uses tenacity for automatic retries on rate limits or transient errors.

        Args:
            system_instruction: The system prompt.
            user_prompt: The specific input prompt.
            response_schema: The Pydantic model class to enforce as the output structure.

        Returns:
            An instance of the requested Pydantic model.
        """
        from backend.llm.providers.base import StructuredOutputSchemaError
        try:
            return self.provider.generate_structured(system_instruction, user_prompt, response_schema)
        except StructuredOutputSchemaError:
            logger.warning("Caught StructuredOutputSchemaError. Retrying exactly once with corrected prompt.")
            correction = (
                "\n\nCRITICAL: You previously returned a JSON Schema definition instead of JSON data. "
                "Return ONLY a JSON DATA object. Do NOT return a schema. "
                "Do NOT include properties, required, type, title, description or other schema metadata."
            )
            return self.provider.generate_structured(system_instruction + correction, user_prompt, response_schema)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def generate_text(self, system_instruction: str, user_prompt: str) -> str:
        """Generate an unstructured text response via the selected provider.

        Args:
            system_instruction: The system prompt.
            user_prompt: The specific input prompt.

        Returns:
            The raw text response.
        """
        return self.provider.generate_text(system_instruction, user_prompt)
