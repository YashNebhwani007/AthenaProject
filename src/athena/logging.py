"""Structured logging configuration for Athena using structlog."""

import logging
import sys
from typing import Any

import structlog

from athena.config import settings


class _DynamicStderr:
    """Dynamic proxy that delegates write/flush calls to current sys.stderr."""

    def write(self, s: str) -> int:
        return sys.stderr.write(s)

    def flush(self) -> None:
        sys.stderr.flush()


def configure_logging(level_name: str | None = None) -> None:
    """Configure structlog with JSON rendering to stderr."""
    effective_level_str = (level_name or settings.log_level).upper()
    level_num = getattr(logging, effective_level_str, logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level_num),
        context_class=dict,
        logger_factory=lambda *args: structlog.PrintLogger(file=_DynamicStderr()),  # type: ignore[arg-type]
        cache_logger_on_first_use=False,
    )


# Configure logging on module import with current settings
configure_logging()


def get_logger(name: str | None = None, **initial_values: Any) -> Any:
    """Return a bound structlog logger.

    Args:
        name: Logger name (typically __name__).
        **initial_values: Key-value context pairs to bind to the logger.
    """
    logger = structlog.get_logger(name)
    if name:
        logger = logger.bind(logger=name)
    if initial_values:
        logger = logger.bind(**initial_values)
    return logger
