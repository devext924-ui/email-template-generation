"""FastAPI dependency providers."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status

from backend.config import Settings, get_settings
from backend.core.pipeline import PipelineArtifacts, PipelineState, get_state


def settings_dep() -> Settings:
    """Return the cached app settings."""

    return get_settings()


def state_dep() -> PipelineState:
    """Return the global pipeline state singleton."""

    return get_state()


def require_artifacts(
    state: PipelineState = Depends(state_dep),
) -> PipelineArtifacts:
    """Return the latest pipeline artifacts or raise 409 if unavailable."""

    artifacts = state.get()
    if artifacts is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pipeline has not been run yet. Call POST /api/run-pipeline first.",
        )
    return artifacts
