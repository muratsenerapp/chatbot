from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import setup_logging, get_logger
from app.services.llm_client import LLMClient
from app.api import register_routers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifecycle: init logging + singleton LLMClient."""
    setup_logging(os.getenv("LOG_LEVEL", "INFO"))
    logger = get_logger()
    app.state.logger = logger
    logger.info("Starting application")

    # create and cache a single LLMClient for the whole app lifetime
    app.state.llm_client = LLMClient(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct"),
    )
    try:
        yield
    finally:
        logger.info("Shutting down application")


app = FastAPI(
    title="Chatbot API",
    version="0.1.0",
    description="FastAPI + Ollama based chat service.",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

register_routers(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
