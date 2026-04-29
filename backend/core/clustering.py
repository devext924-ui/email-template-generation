"""Clustering strategies for email embeddings."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.cluster import DBSCAN, AgglomerativeClustering, KMeans
from sklearn.metrics import davies_bouldin_score, silhouette_score

from backend.config import Settings, get_settings
from backend.core.embeddings import cosine_similarity_matrix
from backend.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ClusteringResult:
    labels: np.ndarray
    n_clusters: int
    method: str
    centroids: Optional[np.ndarray] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    cluster_sizes: Dict[int, int] = field(default_factory=dict)


def _heuristic_k(n_samples: int) -> int:
    """Default cluster count: roughly sqrt(n/2), bounded to a sensible range."""

    return int(np.clip(round(np.sqrt(max(n_samples, 4) / 2)), 4, 20))


def _compute_centroids(embeddings: np.ndarray, labels: np.ndarray) -> np.ndarray:
    unique = sorted({int(c) for c in labels if c != -1})
    centroids = np.zeros((len(unique), embeddings.shape[1]), dtype=np.float32)
    for i, c in enumerate(unique):
        member = embeddings[labels == c]
        centroids[i] = member.mean(axis=0)
    norms = np.linalg.norm(centroids, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return centroids / norms


def _intra_cluster_similarity(embeddings: np.ndarray, labels: np.ndarray) -> float:
    sims: List[float] = []
    for c in {int(x) for x in labels if x != -1}:
        member = embeddings[labels == c]
        if len(member) < 2:
            continue
        sim = cosine_similarity_matrix(member)
        # average of upper-triangular (excluding self-similarity diagonal)
        n = len(member)
        triu_mask = np.triu(np.ones((n, n), dtype=bool), k=1)
        sims.append(float(sim[triu_mask].mean()))
    return float(np.mean(sims)) if sims else 0.0


def _safe_silhouette(embeddings: np.ndarray, labels: np.ndarray) -> Optional[float]:
    valid_labels = labels[labels != -1]
    valid_emb = embeddings[labels != -1]
    if len(set(valid_labels)) < 2 or len(valid_emb) < 3:
        return None
    try:
        return float(silhouette_score(valid_emb, valid_labels, metric="cosine"))
    except Exception as exc:  # pragma: no cover
        logger.warning("Silhouette computation failed: %s", exc)
        return None


def _safe_davies_bouldin(embeddings: np.ndarray, labels: np.ndarray) -> Optional[float]:
    valid_labels = labels[labels != -1]
    valid_emb = embeddings[labels != -1]
    if len(set(valid_labels)) < 2:
        return None
    try:
        return float(davies_bouldin_score(valid_emb, valid_labels))
    except Exception as exc:  # pragma: no cover
        logger.warning("Davies-Bouldin computation failed: %s", exc)
        return None


def cluster_embeddings(
    embeddings: np.ndarray,
    *,
    method: Optional[str] = None,
    n_clusters: Optional[int] = None,
    settings: Optional[Settings] = None,
) -> ClusteringResult:
    """Cluster ``embeddings`` according to the configured method.

    Returns a :class:`ClusteringResult` with labels, centroids, sizes, and
    quality metrics (silhouette, Davies-Bouldin, mean intra-cluster cosine).
    """

    settings = settings or get_settings()
    method = (method or settings.clustering_method).lower()
    n_samples = embeddings.shape[0]
    if n_samples < 2:
        raise ValueError("Need at least 2 embeddings to cluster.")

    if method == "kmeans":
        k = n_clusters or settings.n_clusters or _heuristic_k(n_samples)
        k = max(2, min(k, max(2, n_samples - 1)))
        model = KMeans(n_clusters=k, random_state=settings.random_state, n_init="auto")
        labels = model.fit_predict(embeddings)
        centroids = model.cluster_centers_.astype(np.float32)
        norms = np.linalg.norm(centroids, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        centroids = centroids / norms
    elif method == "agglomerative":
        k = n_clusters or settings.n_clusters or _heuristic_k(n_samples)
        k = max(2, min(k, max(2, n_samples - 1)))
        model = AgglomerativeClustering(n_clusters=k, metric="cosine", linkage="average")
        labels = model.fit_predict(embeddings)
        centroids = _compute_centroids(embeddings, labels)
    elif method == "dbscan":
        # DBSCAN works on cosine distance; pre-normalised embeddings -> use euclidean.
        model = DBSCAN(eps=0.35, min_samples=5, metric="cosine")
        labels = model.fit_predict(embeddings)
        centroids = _compute_centroids(embeddings, labels)
    else:
        raise ValueError(f"Unknown clustering method: {method}")

    unique = [int(c) for c in sorted(set(labels)) if c != -1]
    sizes = {int(c): int((labels == c).sum()) for c in unique}
    metrics = {
        "silhouette_score": _safe_silhouette(embeddings, labels),
        "davies_bouldin_score": _safe_davies_bouldin(embeddings, labels),
        "average_intra_cluster_similarity": _intra_cluster_similarity(embeddings, labels),
    }
    logger.info(
        "Clustering done | method=%s | clusters=%d | metrics=%s",
        method,
        len(unique),
        metrics,
    )
    return ClusteringResult(
        labels=np.asarray(labels, dtype=int),
        n_clusters=len(unique),
        method=method,
        centroids=centroids,
        metrics=metrics,
        cluster_sizes=sizes,
    )
