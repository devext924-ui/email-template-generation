"""Tests for backend.core.embeddings (with the encoder mocked)."""

from __future__ import annotations

import numpy as np

from backend.core.embeddings import (
    EmbeddingModel,
    closest_index,
    cosine_similarity_matrix,
    encode_corpus,
    top_k_indices,
)


def test_encode_returns_normalized_array(deterministic_embedder):
    model = EmbeddingModel()
    out = model.encode(["hello world", "foo bar baz"])
    assert out.shape == (2, 64)
    norms = np.linalg.norm(out, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5)


def test_encode_corpus_caches_to_disk(tmp_path, deterministic_embedder):
    cache = tmp_path / "emb.npy"
    texts = ["alpha beta", "gamma delta"]
    a = encode_corpus(texts, cache_path=cache)
    assert cache.exists()
    b = encode_corpus(texts, cache_path=cache)
    np.testing.assert_array_equal(a, b)


def test_gitkeep_does_not_count_as_fine_tuned_model(tmp_path, monkeypatch):
    from backend.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "fine_tuned_model_dir", tmp_path / "fine_tuned_sentence_transformer")
    settings.fine_tuned_model_dir.mkdir()
    (settings.fine_tuned_model_dir / ".gitkeep").write_text("", encoding="utf-8")

    model = EmbeddingModel(use_fine_tuned=True, settings=settings)

    assert model.is_fine_tuned is False


def test_cosine_matrix_diagonal_is_one(deterministic_embedder):
    model = EmbeddingModel()
    emb = model.encode(["one", "two", "three"])
    sim = cosine_similarity_matrix(emb)
    assert np.allclose(np.diag(sim), 1.0, atol=1e-5)


def test_top_k_indices_returns_self_first(deterministic_embedder):
    model = EmbeddingModel()
    corpus = model.encode(["alpha", "beta", "gamma"])
    query = corpus[1]
    idxs = top_k_indices(query, corpus, k=3)
    assert idxs[0] == 1
    assert closest_index(query, corpus) == 1
