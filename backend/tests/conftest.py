from __future__ import annotations

from collections.abc import Callable

import pytest
from fastapi import FastAPI

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def app_factory() -> Callable[..., FastAPI]:
    """Return a factory that builds FastAPI apps with optional settings overrides."""

    def _factory(**overrides) -> FastAPI:
        settings = Settings(**overrides)
        return create_app(settings=settings)

    return _factory
