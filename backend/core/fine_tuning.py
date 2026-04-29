"""Fine-tuning utilities for the SentenceTransformer encoder.

If supervised category labels are present in the dataset they are used
directly; otherwise we generate pseudo-labels via baseline KMeans on raw
embeddings (weak supervision). Either way we train with
``MultipleNegativesRankingLoss`` over (anchor, positive) pairs.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from backend.config import Settings, get_settings
from backend.core.clustering import cluster_embeddings
from backend.core.embeddings import EmbeddingModel, encode_corpus
from backend.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class FineTuneOutcome:
    model_path: str
    epochs: int
    n_pairs: int
    baseline_silhouette: Optional[float]
    fine_tuned_silhouette: Optional[float]
    duration_seconds: float

    @property
    def improvement(self) -> Optional[float]:
        if self.baseline_silhouette is None or self.fine_tuned_silhouette is None:
            return None
        return self.fine_tuned_silhouette - self.baseline_silhouette


def build_pseudo_labels(texts: List[str], *, settings: Optional[Settings] = None) -> np.ndarray:
    """Generate pseudo-labels via baseline embeddings + KMeans."""

    settings = settings or get_settings()
    model = EmbeddingModel(use_fine_tuned=False, settings=settings)
    embeddings = encode_corpus(texts, model=model, use_cache=True)
    result = cluster_embeddings(embeddings, method="kmeans", settings=settings)
    return result.labels


def build_training_pairs(
    texts: List[str],
    labels,
    *,
    max_per_class: int = 100,
    seed: int = 13,
) -> List[Tuple[str, str]]:
    """Sample positive (anchor, positive) pairs grouped by label.

    Negatives are produced implicitly by ``MultipleNegativesRankingLoss``
    which treats other batch members as negatives.
    """

    rng = random.Random(seed)
    by_label: dict[int, List[int]] = {}
    for idx, lbl in enumerate(labels):
        if lbl == -1:
            continue
        by_label.setdefault(int(lbl), []).append(idx)

    pairs: List[Tuple[str, str]] = []
    for indices in by_label.values():
        if len(indices) < 2:
            continue
        sample = indices if len(indices) <= max_per_class else rng.sample(indices, max_per_class)
        rng.shuffle(sample)
        for i in range(0, len(sample) - 1, 2):
            pairs.append((texts[sample[i]], texts[sample[i + 1]]))
    rng.shuffle(pairs)
    return pairs


def fine_tune_model(
    df: pd.DataFrame,
    *,
    text_column: str = "combined_text",
    label_column: Optional[str] = "category",
    epochs: Optional[int] = None,
    batch_size: Optional[int] = None,
    use_pseudo_labels: bool = True,
    settings: Optional[Settings] = None,
) -> FineTuneOutcome:
    """Fine-tune the configured SentenceTransformer and persist it.

    Returns a :class:`FineTuneOutcome` with before/after silhouette scores
    so callers can decide whether the new model is worth using.
    """

    settings = settings or get_settings()
    epochs = epochs or settings.fine_tune_epochs
    batch_size = batch_size or settings.fine_tune_batch_size
    start = time.perf_counter()

    texts = df[text_column].astype(str).tolist()

    if label_column and label_column in df.columns and df[label_column].notna().any():
        raw_labels = df[label_column].fillna("__missing__").astype(str).tolist()
        unique = {l: i for i, l in enumerate(sorted(set(raw_labels)))}
        labels = np.array([unique[l] for l in raw_labels])
        label_source = "supervised"
    elif use_pseudo_labels:
        logger.info("No category labels found — generating pseudo-labels via clustering")
        labels = build_pseudo_labels(texts, settings=settings)
        label_source = "pseudo"
    else:
        raise ValueError("No labels available and pseudo-labels disabled")

    logger.info("Fine-tuning with %s labels (n=%d)", label_source, len(set(labels)))

    pairs = build_training_pairs(texts, labels)
    if len(pairs) < 2:
        raise ValueError(
            "Not enough training pairs were created. Provide more data or larger label classes."
        )

    # Baseline silhouette
    base_model = EmbeddingModel(use_fine_tuned=False, settings=settings)
    base_emb = encode_corpus(texts, model=base_model, use_cache=False)
    baseline_clusters = cluster_embeddings(base_emb, method="kmeans", settings=settings)
    baseline_silhouette = baseline_clusters.metrics.get("silhouette_score")

    # Fine-tune
    from sentence_transformers import InputExample, SentenceTransformer, losses
    from torch.utils.data import DataLoader

    train_examples = [InputExample(texts=[a, p]) for a, p in pairs]
    model = SentenceTransformer(settings.embedding_model_name)
    train_loader = DataLoader(train_examples, shuffle=True, batch_size=batch_size)
    train_loss = losses.MultipleNegativesRankingLoss(model)
    out_dir = settings.fine_tuned_model_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    model.fit(
        train_objectives=[(train_loader, train_loss)],
        epochs=epochs,
        warmup_steps=settings.fine_tune_warmup_steps,
        output_path=str(out_dir),
        show_progress_bar=False,
    )
    logger.info("Fine-tuned model saved to %s", out_dir)

    # Re-encode and re-evaluate silhouette
    ft_model = EmbeddingModel(use_fine_tuned=True, settings=settings)
    ft_emb = encode_corpus(texts, model=ft_model, use_cache=False)
    ft_clusters = cluster_embeddings(ft_emb, method="kmeans", settings=settings)
    ft_silhouette = ft_clusters.metrics.get("silhouette_score")

    duration = time.perf_counter() - start
    return FineTuneOutcome(
        model_path=str(out_dir),
        epochs=epochs,
        n_pairs=len(pairs),
        baseline_silhouette=baseline_silhouette,
        fine_tuned_silhouette=ft_silhouette,
        duration_seconds=duration,
    )
