"""FastAPI application factory and lifespan management for the Chatbot backend."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import register_routers
from app.core.config import Settings, get_settings
from app.core.logging import get_logger, setup_logging
from app.services.llm import LLMClient, DEFAULT_SYSTEM_PROMPT
from app.services.memory import SessionMemory


def create_lifespan(settings: Settings):
    """Create the application's lifespan context manager.

    Initializes structured logging and a singleton `LLMClient` so handlers can
    reuse shared state across requests.

    Args:
        settings: App configuration used to set log level/CORS and construct the
            LLM client.

    Returns:
        An async context manager compatible with FastAPI's `lifespan` parameter
        that attaches shared objects to `app.state` on startup and cleans up on shutdown.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        setup_logging(level=settings.LOG_LEVEL)
        logger = get_logger("app")
        logger.info("Starting application")

        # Build LLM client with settings-driven generation controls
        model_kwargs = {
            "num_ctx": settings.OLLAMA_NUM_CTX,
            "num_predict": settings.OLLAMA_NUM_PREDICT,
            "top_p": settings.OLLAMA_TOP_P,
            "top_k": settings.OLLAMA_TOP_K,
            "repeat_penalty": settings.OLLAMA_REPEAT_PENALTY,
        }
        # Optional advanced knobs
        if settings.OLLAMA_SEED is not None:
            model_kwargs["seed"] = settings.OLLAMA_SEED
        if settings.OLLAMA_STOP:
            model_kwargs["stop"] = settings.OLLAMA_STOP
        if settings.OLLAMA_MIROSTAT is not None:
            model_kwargs["mirostat"] = settings.OLLAMA_MIROSTAT
        if settings.OLLAMA_MIROSTAT_TAU is not None:
            model_kwargs["mirostat_tau"] = settings.OLLAMA_MIROSTAT_TAU
        if settings.OLLAMA_MIROSTAT_ETA is not None:
            model_kwargs["mirostat_eta"] = settings.OLLAMA_MIROSTAT_ETA

        app.state.settings = settings
        app.state.llm_client = LLMClient(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=settings.OLLAMA_TEMPERATURE,
            model_kwargs=model_kwargs,
            system_prompt=DEFAULT_SYSTEM_PROMPT,
        )
        # Session-scoped in-memory history
        app.state.session_memory = SessionMemory(
            default_system_prompt=app.state.llm_client.system_prompt
        )

        try:
            yield
        finally:
            logger.info("Shutting down application")

    return lifespan


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Applies CORS from settings, registers API routers under ``/api``,
    and wires the lifespan handler.

    Args:
        settings: Optional configuration to use. When ``None``, loads from
             the environment via :func:`get_settings`. Supplying a value eases tests.

    Returns:
        FastAPI: Configured application instance.
    """
    settings = settings or get_settings()
    app = FastAPI(
        title="Chatbot API",
        version="0.1.0",
        description="FastAPI + Ollama based chat service.",
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=create_lifespan(settings),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_routers(app)
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
