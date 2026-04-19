"""Logging configuration using structlog for JSON file output."""

import logging
from pathlib import Path

import structlog

from udg.config import settings


def _setup_logging() -> None:
    """Configure structlog for JSON file output."""
    # Ensure log directory exists
    log_path = Path(settings.log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance.

    Args:
        name: Logger name (typically __name__ from the calling module).

    Returns:
        A structlog-wrapped logger that outputs JSON to settings.log_path.
    """
    _setup_logging()
    return structlog.get_logger(name)


# Initialize on module import
_setup_logging()