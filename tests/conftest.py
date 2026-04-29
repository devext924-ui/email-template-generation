"""Pytest fixtures shared across the test suite.

The heavyweight ML components (SentenceTransformer, transformers
pipelines) are mocked out so that the suite is hermetic and fast.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List
from unittest.mock import patch

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def project_root() -> Path:
    return ROOT


@pytest.fixture
def deterministic_embedder():
    """Patch :class:`EmbeddingModel.encode` to return deterministic vectors.

    The fake encoder embeds each text using a hashed bag-of-words feature
    map, which is enough signal for the clustering and template
    generation tests to behave predictably without downloading models.
    """

    def _fake_encode(self, texts, *, batch_size=None, normalize=True, show_progress_bar=False):
        rng = np.random.default_rng(42)
        dim = 64
        vectors = []
        for t in texts:
            tokens = t.lower().split()
            vec = np.zeros(dim, dtype=np.float32)
            for tok in tokens:
                idx = abs(hash(tok)) % dim
                vec[idx] += 1.0
            if vec.sum() == 0:
                vec = rng.standard_normal(dim).astype(np.float32)
            if normalize:
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm
            vectors.append(vec)
        return np.stack(vectors)

    def _fake_load(self):
        self._model = object()  # sentinel; callers don't introspect it

    with patch("backend.core.embeddings.EmbeddingModel.encode", _fake_encode), \
        patch("backend.core.embeddings.EmbeddingModel._load", _fake_load):
        yield


@pytest.fixture
def tiny_dataframe():
    """Small in-memory dataframe used for unit tests."""

    import pandas as pd

    data = [
        {
            "email_id": "E1",
            "subject": "Meeting request next week",
            "body": "Hi Alex,\n\nCould we schedule a call about the roadmap on Tuesday?\n\nBest,\nJamie",
            "category": "meeting_request",
            "tone": "formal",
            "sentiment": "neutral",
            "sender": "Jamie",
            "recipient": "Alex",
            "created_at": "2024-05-01",
        },
        {
            "email_id": "E2",
            "subject": "Quick sync on roadmap",
            "body": "Hi Sam,\n\nI'd love to set up a 30 minute call about the roadmap. Are you free Wednesday?\n\nThanks,\nRiley",
            "category": "meeting_request",
            "tone": "formal",
            "sentiment": "neutral",
            "sender": "Riley",
            "recipient": "Sam",
            "created_at": "2024-05-02",
        },
        {
            "email_id": "E3",
            "subject": "Issue with billing",
            "body": "Dear Support,\n\nI'm frustrated with the billing discrepancy. Please resolve this by Friday.\n\nRegards,\nPat",
            "category": "complaint",
            "tone": "formal",
            "sentiment": "negative",
            "sender": "Pat",
            "recipient": "Support",
            "created_at": "2024-05-03",
        },
        {
            "email_id": "E4",
            "subject": "Thank you for your help",
            "body": "Hi Maya,\n\nThanks so much for helping with the launch. You really made a difference!\n\nWarm regards,\nDrew",
            "category": "thank_you",
            "tone": "neutral",
            "sentiment": "positive",
            "sender": "Drew",
            "recipient": "Maya",
            "created_at": "2024-05-04",
        },
    ]
    return pd.DataFrame(data)
