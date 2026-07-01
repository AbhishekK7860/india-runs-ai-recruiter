import sys
from time import perf_counter
from pydantic import BaseModel
from backend.llm.client import LLMClient
from backend.core.settings import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class SmokeTestResponse(BaseModel):
    status: str
    number: int

def main():
    settings = get_settings()
    print("=== Phase 1: Configuration Verification ===")
    print(f"LLM_PROVIDER: {settings.LLM_PROVIDER}")
    print(f"OPENROUTER_MODEL: {settings.OPENROUTER_MODEL}")
    print(f"OPENROUTER_API_KEY Present: {bool(settings.OPENROUTER_API_KEY)}")
    print(f"Temperature: {settings.LLM_TEMPERATURE}")
    print(f"Max Tokens: {settings.LLM_MAX_TOKENS}")
    print(f"Timeout: {settings.LLM_TIMEOUT_SEC}")

    print("\n=== Phase 2: Provider Initialization ===")
    try:
        client = LLMClient()
        print("LLMClient initialized successfully.")
    except Exception as e:
        print(f"Initialization failed: {e}")
        sys.exit(1)

    print("\n=== Phase 3: Basic Connectivity Test ===")
    system_prompt = "You are a helpful assistant."
    user_prompt = "Reply with exactly the single word OK."
    try:
        t0 = perf_counter()
        response = client.generate_text(system_prompt, user_prompt)
        t1 = perf_counter()
        print(f"Text Response: {response}")
        print(f"Latency: {t1 - t0:.2f} seconds")
    except Exception as e:
        print(f"Connectivity test failed: {e}")
        sys.exit(1)

    print("\n=== Phase 4: Structured Output Test ===")
    user_prompt_struct = "Return status='working' and number=123"
    try:
        t0 = perf_counter()
        response_struct = client.generate_structured(system_prompt, user_prompt_struct, SmokeTestResponse)
        t1 = perf_counter()
        print(f"Structured Response: {response_struct}")
        print(f"Type: {type(response_struct)}")
        print(f"Latency: {t1 - t0:.2f} seconds")
    except Exception as e:
        print(f"Structured output test failed: {e}")
        sys.exit(1)

    print("\n=== Phase 5: Runtime Report ===")
    print("OpenRouter provider verified successfully. The project is ready for small pipeline testing.")

if __name__ == "__main__":
    main()

