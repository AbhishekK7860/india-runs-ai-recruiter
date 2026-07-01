"""Local LLM Provider placeholder."""

from typing import Any, Type

from backend.llm.providers.base import BaseProvider, T


class LocalProvider(BaseProvider):
    """Placeholder for a local LLM provider."""

    def generate_structured(self, system_instruction: str, user_prompt: str, response_schema: Type[T]) -> T:
        raise NotImplementedError("LocalProvider is not implemented yet.")

    def generate_text(self, system_instruction: str, user_prompt: str) -> str:
        raise NotImplementedError("LocalProvider is not implemented yet.")

    def health_check(self) -> dict[str, Any]:
        return {"status": "error", "details": "LocalProvider is not implemented yet."}
