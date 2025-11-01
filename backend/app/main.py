from contextlib import asynccontextmanager

from fastapi import FastAPI

from api import register_routers
from core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the FastAPI application lifecycle.

    This asynchronous context manager handles startup and shutdown events.
    It initializes the logger during startup and can later be extended to
    manage database connections, cache clients, or other shared resources.

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None: Control is yielded to the running FastAPI application. Code after
        the yield executes during shutdown.

    Example:
        app = FastAPI(lifespan=lifespan)
    """
    logger = setup_logging(level="INFO")
    app.state.logger = logger
    logger.info("Starting application")

    try:
        yield
    finally:
        logger.info("Shutting down application")


app = FastAPI(
    title="Chatbot Backend",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Register routers
register_routers(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
