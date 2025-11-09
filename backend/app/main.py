from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import register_routers
from app.core.config import Settings, get_settings
from app.core.logging import get_logger, setup_logging
from app.services.llm_client import LLMClient


def create_lifespan(settings: Settings):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """App lifecycle: init logging + singleton LLMClient."""

        setup_logging(settings.LOG_LEVEL)
        log = get_logger()
        log.info("Starting application")

        app.state.settings = settings
        app.state.llm_client = LLMClient(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
        )
        try:
            yield
        finally:
            log.info("Shutting down application")

    return lifespan


def create_app(settings: Settings | None = None) -> FastAPI:
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
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_routers(app)
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
