"""Application configuration.

Loads settings from environment variables and .env file using
pydantic-settings. All configuration must be accessed via get_settings().
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "India Runs AI Recruiter"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    GOOGLE_API_KEY: str = ""
    GOOGLE_MODEL: str = ""
    LLM_PROVIDER: str = "openrouter"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = ""
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 4096
    LLM_TIMEOUT_SEC: int = 30
    MAX_CANDIDATES_FAISS: int = 500
    MAX_CANDIDATES_LLM: int = 100
    MAX_CANDIDATES_FINAL: int = 50


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
