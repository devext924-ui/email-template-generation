"""Tests for backend.core.template_generator."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from backend.config import get_settings
from backend.core.clustering import cluster_embeddings
from backend.core.embeddings import EmbeddingModel, encode_corpus
from backend.core.preprocessing import preprocess_dataframe
from backend.core.template_generator import (
    _build_template_text,
    generate_templates,
    save_templates,
)


def test_build_template_text_replaces_dates_and_money():
    text = "Hi Alex,\n\nPlease pay $1,200 by Friday or 12/31/2024. See https://x.com/track\n\nRegards,\nJamie"
    out = _build_template_text(text)
    assert "{date}" in out or "{deadline}" in out
    assert "{amount}" in out
    assert "{link}" in out
    assert "{recipient_name}" in out
    assert "{sender_name}" in out


def test_generate_templates_end_to_end(deterministic_embedder, tmp_path, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "outputs_dir", tmp_path)

    rows = []
    for i in range(20):
        rows.append(
            {
                "email_id": f"M{i}",
                "subject": "Meeting request next week",
                "body": "Hi Alex,\n\nCould we set up a call about the roadmap?\n\nThanks,\nJamie",
                "category": "meeting_request",
                "tone": "formal",
                "sentiment": "neutral",
                "sender": "Jamie",
                "recipient": "Alex",
                "created_at": "2024-05-01",
            }
        )
    for i in range(20):
        rows.append(
            {
                "email_id": f"C{i}",
                "subject": "Issue with billing",
                "body": "Dear Support,\n\nI'm frustrated with the billing discrepancy. Please resolve.\n\nRegards,\nPat",
                "category": "complaint",
                "tone": "formal",
                "sentiment": "negative",
                "sender": "Pat",
                "recipient": "Support",
                "created_at": "2024-05-02",
            }
        )

    df = preprocess_dataframe(pd.DataFrame(rows))
    model = EmbeddingModel()
    emb = encode_corpus(df["combined_text"].tolist(), model=model, use_cache=False)
    clustering = cluster_embeddings(emb, method="kmeans", n_clusters=2)

    templates = generate_templates(df, emb, clustering, embedding_model=model, settings=settings)
    assert 1 <= len(templates) <= 2
    for tpl in templates:
        assert tpl.body_template
        assert tpl.subject_template
        assert "{recipient_name}" in tpl.body_template
        assert tpl.cluster_size > 0

    paths = save_templates(templates, settings=settings)
    assert paths["csv"].exists()
    assert paths["json"].exists()
    assert paths["md"].exists()
    payload = json.loads(paths["json"].read_text())
    assert isinstance(payload, list)
    assert len(payload) == len(templates)


def test_dedup_drops_near_identical_templates(deterministic_embedder, monkeypatch, tmp_path):
    settings = get_settings()
    monkeypatch.setattr(settings, "outputs_dir", tmp_path)
    monkeypatch.setattr(settings, "duplicate_similarity_threshold", 0.5)

    rows = []
    for i in range(30):
        rows.append(
            {
                "email_id": f"X{i}",
                "subject": "Quick question",
                "body": "Hi Sam,\n\nCould you please review the doc?\n\nThanks,\nJordan",
                "category": "request",
                "tone": "neutral",
                "sentiment": "neutral",
                "sender": "Jordan",
                "recipient": "Sam",
                "created_at": "2024-05-04",
            }
        )

    df = preprocess_dataframe(pd.DataFrame(rows))
    model = EmbeddingModel()
    emb = encode_corpus(df["combined_text"].tolist(), model=model, use_cache=False)
    clustering = cluster_embeddings(emb, method="kmeans", n_clusters=3)

    templates = generate_templates(df, emb, clustering, embedding_model=model, settings=settings)
    # All emails are near-duplicates so dedup should collapse them.
    assert len(templates) == 1
