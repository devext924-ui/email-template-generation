"""Sentence Transformer embedding helpers with disk caching.

The :class:`EmbeddingModel` wraps a SentenceTransformer instance so the
rest of the pipeline doesn't need to know about device selection,
batching, or fine-tuned model resolution.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

import numpy as np

from backend.config import Settings, get_settings
from backend.logging_config import get_logger

logger = get_logger(__name__)


class EmbeddingModel:
    """Thin wrapper around ``sentence_transformers.SentenceTransformer``.

    The actual library is imported lazily because it pulls in PyTorch and
    is slow to import; this keeps the test suite fast for components that
    do not require it (e.g., preprocessing).
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        use_fine_tuned: Optional[bool] = None,
        settings: Optional[Settings] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.model_name = model_name or self.settings.embedding_model_name
        self._use_fine_tuned = (
            self._fine_tuned_available()
            if (use_fine_tuned if use_fine_tuned is not None else self.settings.use_fine_tuned)
            else False
        )
        self._model = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _fine_tuned_available(self) -> bool:
        ft = self.settings.fine_tuned_model_dir
        if not ft.exists():
            return False
        return (ft / "config.json").exists() or any(
            p.name != ".gitkeep" and not p.name.startswith(".") for p in ft.iterdir()
        )

    def _load(self) -> None:
        if self._model is not None:
            return
        from sentence_transformers import SentenceTransformer  # lazy import

        target = (
            str(self.settings.fine_tuned_model_dir)
            if self._use_fine_tuned and self._fine_tuned_available()
            else self.model_name
        )
        logger.info("Loading sentence transformer from %s", target)
        self._model = SentenceTransformer(target)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @property
    def is_fine_tuned(self) -> bool:
        return self._use_fine_tuned and self._fine_tuned_available()

    @property
    def model(self):  # type: ignore[no-untyped-def]
        self._load()
        return self._model

    def encode(
        self,
        texts: Sequence[str],
        *,
        batch_size: Optional[int] = None,
        normalize: bool = True,
        show_progress_bar: bool = False,
    ) -> np.ndarray:
        """Encode a batch of texts and return a 2-D numpy array."""

        self._load()
        bs = batch_size or self.settings.embed_batch_size
        embeddings = self._model.encode(  # type: ignore[union-attr]
            list(texts),
            batch_size=bs,
            show_progress_bar=show_progress_bar,
            normalize_embeddings=normalize,
            convert_to_numpy=True,
        )
        return np.asarray(embeddings, dtype=np.float32)


# ---------------------------------------------------------------------------
# Caching helpers
# ---------------------------------------------------------------------------
def _corpus_signature(texts: Iterable[str], model_name: str) -> str:
    h = hashlib.sha256()
    h.update(model_name.encode())
    for t in texts:
        h.update(b"\x1f")
        h.update(t.encode("utf-8", errors="ignore"))
    return h.hexdigest()


def encode_corpus(
    texts: Sequence[str],
    *,
    model: Optional[EmbeddingModel] = None,
    cache_path: Optional[Path] = None,
    use_cache: bool = True,
) -> np.ndarray:
    """Encode ``texts`` with embeddings cached to disk by content hash.

    The cache file stores both the embeddings and the corpus signature,
    so we avoid serving stale embeddings from a previous run.
    """

    settings = get_settings()
    model = model or EmbeddingModel()
    cache_path = cache_path or settings.embedding_cache_file
    sig = _corpus_signature(texts, model.model_name + ("-ft" if model.is_fine_tuned else ""))

    meta_path = cache_path.with_suffix(".meta")
    if use_cache and cache_path.exists() and meta_path.exists():
        try:
            stored_sig = meta_path.read_text().strip()
            if stored_sig == sig:
                arr = np.load(cache_path)
                if arr.shape[0] == len(texts):
                    logger.info("Loaded cached embeddings from %s", cache_path)
                    return arr
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to read embedding cache (%s); regenerating", exc)

    logger.info("Encoding %d texts with %s", len(texts), model.model_name)
    embeddings = model.encode(texts, show_progress_bar=False)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(cache_path, embeddings)
    meta_path.write_text(sig)
    return embeddings


def cosine_similarity_matrix(a: np.ndarray, b: Optional[np.ndarray] = None) -> np.ndarray:
    """Return the pairwise cosine similarity matrix.

    Assumes inputs are already L2-normalized (which :class:`EmbeddingModel`
    does by default).
    """

    if b is None:
        b = a
    return np.clip(a @ b.T, -1.0, 1.0)


def closest_index(query: np.ndarray, corpus: np.ndarray) -> int:
    """Return the index in ``corpus`` most similar to ``query``."""

    if query.ndim == 1:
        query = query[None, :]
    sims = cosine_similarity_matrix(query, corpus)[0]
    return int(np.argmax(sims))


def top_k_indices(query: np.ndarray, corpus: np.ndarray, k: int = 5) -> List[int]:
    if query.ndim == 1:
        query = query[None, :]
    sims = cosine_similarity_matrix(query, corpus)[0]
    return [int(i) for i in np.argsort(-sims)[:k]]
