"""OpenRouter LLM Provider."""

import json
import urllib.error
import urllib.request
from typing import Any, Type

from backend.llm.providers.base import BaseProvider, StructuredOutputError, T
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class OpenRouterProvider(BaseProvider):
    """Provider implementation for OpenRouter compatible APIs."""

    def __init__(self) -> None:
        """Initialize the OpenRouter Provider."""
        from backend.core.settings import get_settings
        self.settings = get_settings()
        self.api_key = self.settings.OPENROUTER_API_KEY
        self.model_name = self.settings.OPENROUTER_MODEL
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def health_check(self) -> dict[str, Any]:
        """Verify OpenRouter connectivity and configuration."""
        if not self.api_key:
            return {"status": "error", "details": "OPENROUTER_API_KEY is missing."}
        
        # Test basic connectivity with a minimal prompt
        try:
            req = urllib.request.Request(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                data=json.dumps({
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 5
                }).encode("utf-8")
            )
            with urllib.request.urlopen(req, timeout=self.settings.LLM_TIMEOUT_SEC) as response:
                if response.status == 200:
                    return {"status": "ok", "details": f"Connected to OpenRouter using {self.model_name}."}
                return {"status": "error", "details": f"Unexpected status: {response.status}"}
        except urllib.error.HTTPError as e:
            return {"status": "error", "details": f"HTTP Error: {e.code} - {e.read().decode('utf-8')}"}
        except Exception as e:
            return {"status": "error", "details": f"Unexpected error: {str(e)}"}

    def _make_request(self, payload: dict[str, Any]) -> str:
        """Internal helper to make the HTTP request."""
        req = urllib.request.Request(
            self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload).encode("utf-8")
        )
        try:
            with urllib.request.urlopen(req, timeout=self.settings.LLM_TIMEOUT_SEC) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            error_msg = e.read().decode("utf-8")
            if e.code == 429:
                # Raise an error that Tenacity can catch and retry
                raise RuntimeError(f"Rate limited (429): {error_msg}")
            elif e.code >= 500:
                raise RuntimeError(f"Server error ({e.code}): {error_msg}")
            else:
                raise ValueError(f"OpenRouter API Error {e.code}: {error_msg}")
        except Exception as e:
            raise RuntimeError(f"Request failed: {str(e)}")

    def generate_structured(self, system_instruction: str, user_prompt: str, response_schema: Type[T]) -> T:
        """Generate a structured response using schema-guided prompting and JSON mode."""
        logger.debug(f"Calling OpenRouter ({self.model_name}) for structured output.")
        
        from backend.llm.schema_utils import simplify_schema, parse_and_recover
        fields_str, example_str, expected_root = simplify_schema(response_schema)
        
        augmented_system = (
            f"{system_instruction}\n\n"
            f"You must respond with a JSON DATA OBJECT. Do NOT return a JSON SCHEMA.\n"
            f"Your output must contain exactly the following fields:\n"
            f"{fields_str}\n\n"
            f"Example Output Structure:\n"
            f"{example_str}\n\n"
            f"Do NOT include properties, required, definitions, $schema, type, title, or description unless they are actual business fields.\n"
            f"Return exactly one JSON object. No markdown. No code fences. No explanations. No prose."
        )

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": augmented_system},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.settings.LLM_TEMPERATURE,
            "max_tokens": self.settings.LLM_MAX_TOKENS,
            "response_format": {"type": "json_object"}
        }

        response_text = self._make_request(payload)
        
        try:
            return parse_and_recover(response_text, expected_root, response_schema)
        except Exception as e:
            logger.error(f"Failed to parse OpenRouter response into schema. Raw response: {response_text}")
            raise e

    def generate_text(self, system_instruction: str, user_prompt: str) -> str:
        """Generate unstructured text response."""
        logger.debug(f"Calling OpenRouter ({self.model_name}) for text output.")
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.settings.LLM_TEMPERATURE,
            "max_tokens": self.settings.LLM_MAX_TOKENS,
        }
        return self._make_request(payload)
