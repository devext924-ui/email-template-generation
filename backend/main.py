"""FastAPI application entry point.

Run with::

    uvicorn backend.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend import __version__
from backend.api.routes import router as api_router
from backend.config import get_settings
from backend.logging_config import configure_logging, get_logger


def create_app() -> FastAPI:
    """Application factory."""

    configure_logging()
    settings = get_settings()
    logger = get_logger(__name__)

    @asynccontextmanager
    async def _lifespan(app: FastAPI):  # pragma: no cover - trivial
        settings.ensure_directories()
        logger.info("%s started — env=%s", settings.app_name, settings.app_env)
        yield

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "Production-ready ML pipeline for clustering raw email datasets and "
            "generating reusable, professional email templates."
        ),
        lifespan=_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    return app


app = create_app()
