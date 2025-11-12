"""Logging utilities for consistent, project-wide logging configuration and retrieval."""

import logging
from logging import Logger

LOGGER_NAME = "chatbot"


def setup_logging(level: str = "INFO") -> Logger:
    """Configure and initialize the global logging system for the application.

    This function sets up a project-level logger (`chatbot`) with a consistent
    format and integrates with Uvicorn's built-in loggers to ensure unified
    formatting and levels across the stack.

    The setup is idempotent — calling this function multiple times will not
    attach duplicate handlers.

    Args:
        level (str): Logging level as a string (e.g., "INFO", "DEBUG", "ERROR").
            Must correspond to a valid level constant from the `logging` module.

    Returns:
        Logger: The configured root logger for the application.

    Raises:
        ValueError: If the provided log level string is invalid.
    """
    level = level.upper()

    if not hasattr(logging, level):
        valid_levels = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]
        raise ValueError(
            f"Invalid log level: '{level}'. Must be one of {valid_levels}."
        )

    numeric_level = getattr(logging, level)
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(numeric_level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uv_logger = logging.getLogger(name)
        uv_logger.setLevel(numeric_level)
        uv_logger.propagate = True

    logger.propagate = False
    return logger


def get_logger(name: str | None = None) -> Logger:
    """Retrieve a child logger derived from the main project logger.

    This allows modules (e.g., services, API routes) to use a contextual logger
    under the main project namespace, ensuring consistent formatting and
    configuration.

    Args:
        name (str | None): Optional sub-name for the child logger. For example,
            passing "services.db" creates a logger named "chatbot.services.db".
            If None, the root "chatbot" logger is returned.

    Returns:
        Logger: A configured child logger instance.

    Example:
        >>> from app.core.logging import get_logger
        >>> logger = get_logger("services.db")
        >>> logger.info("Database connection established")
    """
    full_name = LOGGER_NAME if not name else f"{LOGGER_NAME}.{name}"
    return logging.getLogger(full_name)
