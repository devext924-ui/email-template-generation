"""Centralised logging configuration."""

from __future__ import annotations

import logging
import sys
from logging.config import dictConfig

from backend.config import get_settings


def configure_logging() -> None:
    """Configure root logger formatting based on the app log level."""

    settings = get_settings()

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": sys.stdout,
                    "formatter": "default",
                    "level": settings.log_level,
                }
            },
            "root": {"handlers": ["console"], "level": settings.log_level},
            "loggers": {
                "uvicorn.error": {"level": settings.log_level},
                "uvicorn.access": {"level": settings.log_level},
                "sentence_transformers": {"level": "WARNING"},
                "transformers": {"level": "WARNING"},
            },
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger after ensuring config has been applied."""

    if not logging.getLogger().handlers:
        configure_logging()
    return logging.getLogger(name)
