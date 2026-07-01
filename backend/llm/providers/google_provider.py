"""Google GenAI LLM Provider."""

from typing import Any, Type

from google import genai
from google.genai.errors import APIError

from backend.llm.providers.base import BaseProvider, StructuredOutputError, T
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class GoogleProvider(BaseProvider):
    """Provider implementation for Google Gemini via SDK."""

    def __init__(self) -> None:
        """Initialize the Google Provider."""
        from backend.core.settings import get_settings
        self.settings = get_settings()
        self.api_key = self.settings.GOOGLE_API_KEY
        self.model_name = self.settings.GOOGLE_MODEL

        if not self.api_key:
            logger.warning("GOOGLE_API_KEY is not set. Google Provider will fail health check.")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)

    def health_check(self) -> dict[str, Any]:
        """Verify Google GenAI configuration and connectivity."""
        if not self.api_key:
            return {"status": "error", "details": "GOOGLE_API_KEY is missing."}
        if not self.client:
            return {"status": "error", "details": "Client failed to initialize."}
            
        try:
            # Just do a very lightweight call to test API key (e.g., list models or a tiny prompt)
            models = self.client.models.list()
            model_exists = any(m.name == f"models/{self.model_name}" or m.name == self.model_name for m in models)
            if not model_exists:
                return {"status": "warning", "details": f"Model {self.model_name} might not exist."}
            return {"status": "ok", "details": "Connected to Google GenAI."}
        except APIError as e:
            return {"status": "error", "details": f"API Error: {str(e)}"}
        except Exception as e:
            return {"status": "error", "details": f"Unexpected error: {str(e)}"}

    def generate_structured(self, system_instruction: str, user_prompt: str, response_schema: Type[T]) -> T:
        """Generate a structured response using Gemini JSON Mode."""
        if not self.client:
            raise RuntimeError("GoogleProvider client is not initialized.")
            
        logger.debug(f"Calling Google ({self.model_name}) for structured output.")

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=self.settings.LLM_TEMPERATURE,
            ),
        )

        try:
            from backend.llm.schema_utils import parse_and_recover, simplify_schema
            _, _, expected_root = simplify_schema(response_schema)
            return parse_and_recover(response.text, expected_root, response_schema)
        except Exception as e:
            logger.error(f"Failed to parse Google response into schema. Raw response: {response.text}")
            raise e

    def generate_text(self, system_instruction: str, user_prompt: str) -> str:
        """Generate raw text response."""
        if not self.client:
            raise RuntimeError("GoogleProvider client is not initialized.")

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=self.settings.LLM_TEMPERATURE,
            ),
        )
        return response.text
