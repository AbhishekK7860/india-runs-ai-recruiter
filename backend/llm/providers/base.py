"""Abstract Base Provider for LLM clients."""

from abc import ABC, abstractmethod
from typing import Any, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class StructuredOutputError(Exception):
    """Raised when the LLM output cannot be parsed into the expected structure."""
    pass

class StructuredOutputSchemaError(StructuredOutputError):
    """Raised when the LLM outputs a JSON Schema instead of a data object."""
    pass

class BaseProvider(ABC):
    """Abstract interface for all LLM providers."""

    @abstractmethod
    def generate_structured(self, system_instruction: str, user_prompt: str, response_schema: Type[T]) -> T:
        """Generate a structured response matching a Pydantic schema.

        Args:
            system_instruction: The system prompt.
            user_prompt: The specific input prompt.
            response_schema: The Pydantic model class to enforce.

        Returns:
            An instance of the requested Pydantic model.
        """
        pass

    @abstractmethod
    def generate_text(self, system_instruction: str, user_prompt: str) -> str:
        """Generate unstructured text response.

        Args:
            system_instruction: The system prompt.
            user_prompt: The specific input prompt.

        Returns:
            The raw text response.
        """
        pass

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        """Verify provider connectivity, API key validity, and model availability.

        Returns:
            A dictionary containing health status information.
            Must include at minimum: {"status": "ok" | "error", "details": str}
        """
        pass
