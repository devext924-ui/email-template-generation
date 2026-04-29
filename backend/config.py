"""Application configuration loaded from environment variables.

All settings are resolved relative to the project root so the backend can be
launched from any working directory without breaking path lookups.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _resolve(path: str | Path) -> Path:
    """Return an absolute path, resolving relative entries against the project root."""

    p = Path(path)
    return p if p.is_absolute() else (PROJECT_ROOT / p).resolve()


class Settings(BaseSettings):
    """Typed configuration object backed by `.env`."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Email Template Generation"
    app_env: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"

    data_dir: Path = Field(default=Path("data"))
    raw_data_dir: Path = Field(default=Path("data/raw"))
    processed_data_dir: Path = Field(default=Path("data/processed"))
    models_dir: Path = Field(default=Path("models"))
    outputs_dir: Path = Field(default=Path("outputs"))
    sample_csv: Path = Field(default=Path("data/sample_emails.csv"))

    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    fine_tuned_model_dir: Path = Field(
        default=Path("models/fine_tuned_sentence_transformer")
    )
    embedding_cache_file: Path = Field(default=Path("data/processed/embeddings.npy"))
    use_fine_tuned: bool = False
    embed_batch_size: int = 64

    clustering_method: Literal["kmeans", "dbscan", "agglomerative"] = "kmeans"
    n_clusters: Optional[int] = None
    random_state: int = 42

    fine_tune_epochs: int = 1
    fine_tune_batch_size: int = 16
    fine_tune_warmup_steps: int = 50

    max_templates: int = 50
    duplicate_similarity_threshold: float = 0.92

    sentiment_backend: Literal["rule_based", "transformer"] = "rule_based"

    @field_validator(
        "data_dir",
        "raw_data_dir",
        "processed_data_dir",
        "models_dir",
        "outputs_dir",
        "sample_csv",
        "fine_tuned_model_dir",
        "embedding_cache_file",
        mode="after",
    )
    @classmethod
    def _resolve_path(cls, value: Path) -> Path:
        return _resolve(value)

    def ensure_directories(self) -> None:
        """Create core directories on disk if they do not yet exist."""

        for path in (
            self.data_dir,
            self.raw_data_dir,
            self.processed_data_dir,
            self.models_dir,
            self.outputs_dir,
            self.fine_tuned_model_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    settings = Settings()
    settings.ensure_directories()
    return settings
