from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # General
    LOG_LEVEL: str = "INFO"
    ALLOW_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])

    # Ollama connectivity
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b-instruct"

    # Generation controls (safe defaults; see notes)
    OLLAMA_TEMPERATURE: float = 0.2
    OLLAMA_TOP_P: float = 0.9
    OLLAMA_TOP_K: int = 40
    OLLAMA_REPEAT_PENALTY: float = 1.1
    OLLAMA_NUM_CTX: int = 4096
    OLLAMA_NUM_PREDICT: int = 512
    OLLAMA_SEED: Optional[int] = None
    # Comma-separated or JSON array in env, pydantic will parse list[str]
    OLLAMA_STOP: list[str] = Field(default_factory=list)

    # Advanced (optional)
    OLLAMA_MIROSTAT: Optional[int] = None  # 0/1/2
    OLLAMA_MIROSTAT_TAU: Optional[float] = None
    OLLAMA_MIROSTAT_ETA: Optional[float] = None

    model_config = SettingsConfigDict(env_file=(".env",), env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    """Return a cached instance of the application settings."""
    return Settings()
