"""Structured logging configuration for the India Runs AI Recruiter.

Configures structlog with dev-friendly ConsoleRenderer in development
and JSONRenderer in all other environments. Call get_logger(__name__)
in any module to obtain a pre-configured bound logger.
"""

import logging
import sys

import structlog

from backend.core.settings import get_settings

_SETTINGS = get_settings()


def _configure_logging() -> None:
    """Configure structlog processors based on the current environment."""
    shared_processors: list[structlog.types.Processor] = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if _SETTINGS.ENVIRONMENT == "development":
        renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(_SETTINGS.LOG_LEVEL.upper())


# Configure once at module import time.
_configure_logging()


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structlog BoundLogger bound to the given module name.

    Args:
        name: Typically __name__ of the calling module.

    Returns:
        A configured BoundLogger instance.
    """
    return structlog.get_logger(name)
