"""API router registration for the Chatbot backend."""

from fastapi import FastAPI
from .health import router as health_router
from .chat import router as chat_router

__all__ = ("register_routers",)


def register_routers(app: FastAPI) -> None:
    """Register application API routers under the `/api` prefix.

    Centralizes router wiring to simplify app composition and testing.

    Args:
        app: FastAPI instance to attach routes to.
    """
    routers = [health_router, chat_router]
    for r in routers:
        app.include_router(r, prefix="/api")
