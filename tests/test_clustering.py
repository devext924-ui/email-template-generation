"""Tests for backend.core.clustering."""

from __future__ import annotations

import numpy as np
import pytest

from backend.core.clustering import cluster_embeddings


def _two_blobs(n_per_cluster: int = 30, dim: int = 8, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    a = rng.normal(loc=1.0, scale=0.05, size=(n_per_cluster, dim))
    b = rng.normal(loc=-1.0, scale=0.05, size=(n_per_cluster, dim))
    arr = np.vstack([a, b]).astype(np.float32)
    arr /= np.linalg.norm(arr, axis=1, keepdims=True)
    return arr


def test_kmeans_finds_two_clusters():
    emb = _two_blobs()
    res = cluster_embeddings(emb, method="kmeans", n_clusters=2)
    assert res.n_clusters == 2
    # Each cluster should contain about half the points
    sizes = sorted(res.cluster_sizes.values())
    assert sizes[0] > 20 and sizes[1] > 20
    assert res.metrics["silhouette_score"] is not None
    assert res.metrics["silhouette_score"] > 0.5


def test_agglomerative_method_returns_centroids():
    emb = _two_blobs()
    res = cluster_embeddings(emb, method="agglomerative", n_clusters=2)
    assert res.method == "agglomerative"
    assert res.centroids is not None
    assert res.centroids.shape == (2, emb.shape[1])


def test_dbscan_returns_metrics_or_noise():
    emb = _two_blobs(n_per_cluster=40)
    res = cluster_embeddings(emb, method="dbscan")
    assert res.method == "dbscan"
    assert isinstance(res.cluster_sizes, dict)


def test_invalid_method_raises():
    emb = _two_blobs()
    with pytest.raises(ValueError):
        cluster_embeddings(emb, method="not-a-real-method")
