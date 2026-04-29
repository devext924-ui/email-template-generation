"""Tests for backend.core.evaluation."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backend.config import get_settings
from backend.core.clustering import cluster_embeddings
from backend.core.embeddings import EmbeddingModel, encode_corpus
from backend.core.evaluation import evaluate
from backend.core.preprocessing import preprocess_dataframe
from backend.core.template_generator import generate_templates


def test_evaluate_reports_expected_keys(deterministic_embedder, monkeypatch, tmp_path):
    settings = get_settings()
    monkeypatch.setattr(settings, "outputs_dir", tmp_path)

    rows = []
    for i in range(40):
        cat = "meeting_request" if i % 2 == 0 else "complaint"
        body = (
            "Hi Alex,\n\nLet's schedule the roadmap meeting.\n\nThanks,\nJamie"
            if cat == "meeting_request"
            else "Dear Support,\n\nIssue with the billing discrepancy.\n\nRegards,\nPat"
        )
        rows.append(
            {
                "email_id": f"E{i}",
                "subject": "Sample subject",
                "body": body,
                "category": cat,
                "tone": "formal",
                "sentiment": "neutral",
                "sender": "Jamie",
                "recipient": "Alex",
                "created_at": "2024-05-01",
            }
        )
    df = preprocess_dataframe(pd.DataFrame(rows))
    model = EmbeddingModel()
    emb = encode_corpus(df["combined_text"].tolist(), model=model, use_cache=False)
    clustering = cluster_embeddings(emb, method="kmeans", n_clusters=2)
    templates = generate_templates(df, emb, clustering, embedding_model=model, settings=settings)

    metrics = evaluate(
        n_emails=len(df),
        embeddings=emb,
        clustering=clustering,
        templates=templates,
        baseline_silhouette=0.4,
        fine_tuned_silhouette=0.5,
    )
    expected_keys = {
        "n_emails",
        "n_clusters",
        "n_templates",
        "silhouette_score",
        "davies_bouldin_score",
        "average_intra_cluster_similarity",
        "cluster_sizes",
        "template_coverage",
        "duplicate_template_percentage",
        "average_template_length",
        "fine_tuning_improvement",
    }
    assert expected_keys.issubset(metrics.keys())
    assert metrics["fine_tuning_improvement"] == pytest.approx(0.1)
    assert 0.0 <= metrics["template_coverage"] <= 1.0
