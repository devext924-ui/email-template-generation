"""End-to-end pipeline orchestration.

The :class:`PipelineState` singleton holds the most recent run's
artifacts (DataFrame, embeddings, clustering, templates, evaluation) so
the API can serve them without rerunning the full pipeline.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from backend.config import Settings, get_settings
from backend.core.clustering import ClusteringResult, cluster_embeddings
from backend.core.data_loader import ensure_dataset, load_csv, save_processed
from backend.core.embeddings import EmbeddingModel, encode_corpus, top_k_indices
from backend.core.evaluation import evaluate
from backend.core.preprocessing import preprocess_dataframe
from backend.core.sentiment import SentimentAnalyzer
from backend.core.template_generator import (
    GeneratedTemplate,
    generate_templates,
    save_templates,
)
from backend.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class PipelineArtifacts:
    df: pd.DataFrame
    embeddings: np.ndarray
    clustering: ClusteringResult
    templates: List[GeneratedTemplate]
    evaluation: Dict[str, Any]
    output_paths: Dict[str, Path]
    embedding_model: EmbeddingModel
    duration_seconds: float
    csv_source: Optional[str] = None
    fine_tuned_used: bool = False


@dataclass
class PipelineState:
    """Mutable in-memory store for the latest pipeline run."""

    artifacts: Optional[PipelineArtifacts] = None
    last_uploaded_csv: Optional[Path] = None
    lock: threading.Lock = field(default_factory=threading.Lock)

    def set(self, artifacts: PipelineArtifacts) -> None:
        with self.lock:
            self.artifacts = artifacts

    def get(self) -> Optional[PipelineArtifacts]:
        with self.lock:
            return self.artifacts

    def get_template(self, template_id: str) -> Optional[GeneratedTemplate]:
        artifacts = self.get()
        if not artifacts:
            return None
        for tpl in artifacts.templates:
            if tpl.template_id == template_id:
                return tpl
        return None


_state = PipelineState()


def get_state() -> PipelineState:
    """Return the global pipeline state singleton."""

    return _state


# ---------------------------------------------------------------------------
# Pipeline entry point
# ---------------------------------------------------------------------------
def run_pipeline(
    *,
    csv_path: Optional[str | Path] = None,
    use_fine_tuned: Optional[bool] = None,
    n_clusters: Optional[int] = None,
    clustering_method: Optional[str] = None,
    settings: Optional[Settings] = None,
) -> PipelineArtifacts:
    """Execute the full pipeline and return the artifacts.

    Steps: load → preprocess → embed → cluster → enrich (sentiment/tone)
    → generate templates → evaluate → persist outputs.
    """

    settings = settings or get_settings()
    start = time.perf_counter()

    df = ensure_dataset(csv_path) if csv_path else _resolve_default_dataset(settings)
    df = preprocess_dataframe(df)
    save_processed(df, name="cleaned_emails.csv")

    # Sentiment / tone enrichment
    analyzer = SentimentAnalyzer(settings=settings)
    sentiment_results = analyzer.analyze_many(df["combined_text"].tolist())
    if df["sentiment"].isna().all():
        df["sentiment"] = [r.sentiment for r in sentiment_results]
    if df["tone"].isna().all():
        df["tone"] = [r.tone for r in sentiment_results]

    # Embeddings
    model = EmbeddingModel(use_fine_tuned=use_fine_tuned, settings=settings)
    embeddings = encode_corpus(df["combined_text"].tolist(), model=model, use_cache=True)

    # Clustering
    clustering = cluster_embeddings(
        embeddings,
        method=clustering_method,
        n_clusters=n_clusters,
        settings=settings,
    )

    # Templates
    templates = generate_templates(
        df, embeddings, clustering, settings=settings, embedding_model=model
    )
    output_paths = save_templates(templates, settings=settings)

    metrics = evaluate(
        n_emails=len(df),
        embeddings=embeddings,
        clustering=clustering,
        templates=templates,
    )

    duration = time.perf_counter() - start
    artifacts = PipelineArtifacts(
        df=df,
        embeddings=embeddings,
        clustering=clustering,
        templates=templates,
        evaluation=metrics,
        output_paths=output_paths,
        embedding_model=model,
        duration_seconds=duration,
        csv_source=str(csv_path) if csv_path else None,
        fine_tuned_used=model.is_fine_tuned,
    )
    _state.set(artifacts)
    logger.info("Pipeline finished in %.2fs", duration)
    return artifacts


def _resolve_default_dataset(settings: Settings) -> pd.DataFrame:
    """Pick the most recently uploaded CSV, then sample, then synthesise."""

    if _state.last_uploaded_csv and Path(_state.last_uploaded_csv).exists():
        return load_csv(_state.last_uploaded_csv)
    return ensure_dataset()


# ---------------------------------------------------------------------------
# Inference helper for "match my email to a template"
# ---------------------------------------------------------------------------
def match_template(
    body: str,
    *,
    subject: Optional[str] = None,
    top_k: int = 1,
) -> List[Dict[str, Any]]:
    """Return the closest template(s) to a raw email."""

    artifacts = _state.get()
    if not artifacts or not artifacts.templates:
        raise RuntimeError("Pipeline has not been run yet — no templates available.")

    from backend.utils.text_utils import build_combined_text

    query_text = build_combined_text(subject or "", body)
    template_texts = [
        f"{t.subject_template}\n\n{t.body_template}" for t in artifacts.templates
    ]
    template_embs = artifacts.embedding_model.encode(template_texts)
    query_emb = artifacts.embedding_model.encode([query_text])[0]
    indices = top_k_indices(query_emb, template_embs, k=min(top_k, len(template_texts)))
    sims = (query_emb @ template_embs.T)
    return [
        {"template": artifacts.templates[i], "similarity": float(sims[i])} for i in indices
    ]
