from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    LOG_LEVEL: str = "INFO"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b-instruct"
    ALLOW_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])

    model_config = SettingsConfigDict(env_file=(".env",), env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    """Return a cached instance of the application settings."""

    return Settings()
