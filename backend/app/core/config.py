"""Configuration primitives for the Chatbot backend powered by Pydantic settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    Attributes:
        LOG_LEVEL: Minimum log level.
        ALLOW_ORIGINS: Allowed CORS origins; use ``*`` to allow all.
        OLLAMA_BASE_URL: Base URL of the Ollama server.
        OLLAMA_MODEL: Default model name/tag on the Ollama server.
        OLLAMA_TEMPERATURE: Sampling temperature (higher = more random).
        OLLAMA_TOP_P: Nucleus sampling threshold.
        OLLAMA_TOP_K: Top-k sampling limit.
        OLLAMA_REPEAT_PENALTY: Repetition penalty factor.
        OLLAMA_NUM_CTX: Context window size (input tokens).
        OLLAMA_NUM_PREDICT: Max tokens to generate.
        OLLAMA_SEED: Optional deterministic seed for reproducibility.
        OLLAMA_STOP: Stop sequences; can be a comma-separated or JSON array in env.
        OLLAMA_MIROSTAT: Mirostat mode (0/1/2) if enabled.
        OLLAMA_MIROSTAT_TAU: Target surprise parameter for Mirostat.
        OLLAMA_MIROSTAT_ETA: Learning rate parameter for Mirostat.
    """

    # General
    LOG_LEVEL: str = "INFO"
    ALLOW_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

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
    OLLAMA_SEED: int | None = None
    # Comma-separated or JSON array in env, pydantic will parse list[str]
    OLLAMA_STOP: list[str] = Field(default_factory=list)

    # Advanced (optional)
    OLLAMA_MIROSTAT: int | None = None  # 0/1/2
    OLLAMA_MIROSTAT_TAU: float | None = None
    OLLAMA_MIROSTAT_ETA: float | None = None


@lru_cache
def get_settings() -> Settings:
    """Return a cached instance of the application settings."""
    return Settings()
