"""Aggregated evaluation metrics for the pipeline."""

from __future__ import annotations

import contextlib
import io
from typing import Any, Dict, List, Optional

import numpy as np

from backend.core.clustering import ClusteringResult
from backend.core.embeddings import cosine_similarity_matrix
from backend.core.template_generator import GeneratedTemplate
from backend.logging_config import get_logger

logger = get_logger(__name__)


def _readability(text: str) -> Optional[float]:
    try:
        # Some textstat/NLTK installs try to fetch optional corpora at runtime.
        # Keep that optional path from polluting CLI/API output in offline setups.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            import textstat  # type: ignore

            return float(textstat.flesch_reading_ease(text))
    except Exception:  # pragma: no cover - optional dependency
        return None


def _avg(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return float(sum(values) / len(values))


def evaluate(
    *,
    n_emails: int,
    embeddings: np.ndarray,
    clustering: ClusteringResult,
    templates: List[GeneratedTemplate],
    baseline_silhouette: Optional[float] = None,
    fine_tuned_silhouette: Optional[float] = None,
) -> Dict[str, Any]:
    """Compute the consolidated metric report used by the API."""

    template_count = len(templates)
    covered = sum(t.cluster_size for t in templates)
    coverage = covered / n_emails if n_emails else 0.0

    duplicate_pct = 0.0
    if template_count > 1:
        bodies = np.array([t.body_template for t in templates])
        # Compare placeholders+intent overlap; exact body duplicates are a stronger signal
        seen = {}
        dups = 0
        for body in bodies:
            key = body.strip().lower()
            if key in seen:
                dups += 1
            else:
                seen[key] = True
        duplicate_pct = dups / template_count

    avg_template_length = _avg([len(t.body_template) for t in templates]) or 0.0
    readability_scores = [r for r in (_readability(t.body_template) for t in templates) if r is not None]
    avg_readability = _avg(readability_scores)

    cluster_sizes = {str(k): int(v) for k, v in clustering.cluster_sizes.items()}

    metrics = {
        "n_emails": int(n_emails),
        "n_clusters": int(clustering.n_clusters),
        "n_templates": int(template_count),
        "silhouette_score": clustering.metrics.get("silhouette_score"),
        "davies_bouldin_score": clustering.metrics.get("davies_bouldin_score"),
        "average_intra_cluster_similarity": clustering.metrics.get(
            "average_intra_cluster_similarity"
        ),
        "cluster_sizes": cluster_sizes,
        "template_coverage": float(coverage),
        "duplicate_template_percentage": float(duplicate_pct),
        "average_template_length": float(avg_template_length),
        "average_readability": avg_readability,
        "baseline_silhouette": baseline_silhouette,
        "fine_tuned_silhouette": fine_tuned_silhouette,
        "fine_tuning_improvement": (
            None
            if (baseline_silhouette is None or fine_tuned_silhouette is None)
            else fine_tuned_silhouette - baseline_silhouette
        ),
    }
    logger.info("Evaluation: %s", metrics)
    return metrics
