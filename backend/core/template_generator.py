"""Generate reusable email templates from clustered emails.

Strategy per cluster:
1. Pick the email closest to the cluster centroid as the representative.
2. Replace variable content (names, dates, deadlines, money, URLs, IDs)
   with placeholder tokens.
3. Standardise greetings and closings.
4. Produce both subject and body templates.
5. De-duplicate templates that are too similar to each other (cosine
   similarity threshold from settings).
"""

from __future__ import annotations

import hashlib
import re
import uuid
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from backend.config import Settings, get_settings
from backend.core.clustering import ClusteringResult
from backend.core.embeddings import EmbeddingModel, cosine_similarity_matrix, encode_corpus
from backend.logging_config import get_logger
from backend.utils import text_utils as tu
from backend.utils.file_utils import write_json

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Placeholder substitution
# ---------------------------------------------------------------------------
_REPLACEMENTS = [
    # Dates
    (re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"), "{date}"),
    (
        re.compile(
            r"\b(?:on\s+)?(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:,?\s*\d{2,4})?\b",
            re.IGNORECASE,
        ),
        "{date}",
    ),
    (
        re.compile(
            r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
            re.IGNORECASE,
        ),
        "{date}",
    ),
    # Deadlines
    (re.compile(r"\bby\s+(?:end\s+of\s+\w+|EOD|EOW|next\s+\w+|tomorrow|\w+day)\b", re.IGNORECASE), "by {deadline}"),
    # Money / invoice numbers
    (re.compile(r"\$\d+(?:[,.]\d+)*"), "{amount}"),
    (re.compile(r"\bINV-\d{3,}\b"), "{invoice_no}"),
    # URLs and emails
    (re.compile(r"https?://\S+"), "{link}"),
    (re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b"), "{email}"),
    # Phone numbers
    (re.compile(r"\b\+?\d[\d\-\s]{7,}\d\b"), "{phone}"),
    # Companies
    (
        re.compile(
            r"\b[A-Z][A-Za-z&\.\s]{2,30}(?:Inc|LLC|Ltd|Corp|Co\.|Corporation|Company)\b"
        ),
        "{company_name}",
    ),
]

_GREETING_RE = re.compile(
    r"^[ \t]*(?:hi|hello|hey|dear|greetings)[ \t,]+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)[!,]?[ \t]*",
    re.IGNORECASE,
)
_CLOSING_NAME_RE = re.compile(
    r"\b(best regards|kind regards|warm regards|sincerely|regards|thanks|thank you|cheers),?\s*\n+\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)",
    re.IGNORECASE,
)


def _placeholderize(text: str) -> str:
    """Apply structural placeholder substitutions (dates, money, URLs)."""

    out = text
    for pattern, replacement in _REPLACEMENTS:
        out = pattern.sub(replacement, out)
    return out


def _normalize_greeting(text: str) -> str:
    return _GREETING_RE.sub("Hi {recipient_name},", text, count=1)


def _normalize_closing(text: str) -> str:
    return _CLOSING_NAME_RE.sub(
        lambda m: f"{m.group(1).title()},\n{{sender_name}}", text, count=1
    )


def _extract_placeholders(text: str) -> List[str]:
    return sorted(set(re.findall(r"\{([a-zA-Z_]+)\}", text)))


def _summarise_placeholder_targets(text: str) -> List[str]:
    """Return a list of placeholders that *should* be in the template body."""

    detected = set(_extract_placeholders(text))
    # Always include recipient/sender if greeting/closing standardised
    detected.update({"recipient_name", "sender_name"})
    return sorted(detected)


# ---------------------------------------------------------------------------
# Template generation
# ---------------------------------------------------------------------------
@dataclass
class GeneratedTemplate:
    template_id: str
    cluster_id: int
    cluster_size: int
    category: Optional[str]
    tone: Optional[str]
    sentiment: Optional[str]
    intent: Optional[str]
    subject_template: str
    body_template: str
    placeholders: List[str]
    representative_email_id: Optional[str]
    similarity_to_centroid: Optional[float]
    common_phrases: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "cluster_id": self.cluster_id,
            "cluster_size": self.cluster_size,
            "category": self.category,
            "tone": self.tone,
            "sentiment": self.sentiment,
            "intent": self.intent,
            "subject_template": self.subject_template,
            "body_template": self.body_template,
            "placeholders": self.placeholders,
            "representative_email_id": self.representative_email_id,
            "similarity_to_centroid": self.similarity_to_centroid,
            "common_phrases": self.common_phrases,
        }


def _majority_label(values: List[Optional[str]]) -> Optional[str]:
    cleaned = [v for v in values if v]
    if not cleaned:
        return None
    return Counter(cleaned).most_common(1)[0][0]


def _build_template_text(text: str) -> str:
    text = _placeholderize(text)
    text = _normalize_greeting(text)
    text = _normalize_closing(text)
    text = tu.normalize_whitespace(text)
    return text


def _build_subject_template(subject: str) -> str:
    return tu.normalize_whitespace(_placeholderize(subject)) or "Regarding {topic}"


def _representative_index(
    embeddings: np.ndarray, indices: List[int], centroid: np.ndarray
) -> tuple[int, float]:
    member = embeddings[indices]
    sims = cosine_similarity_matrix(member, centroid[None, :])[:, 0]
    best = int(np.argmax(sims))
    return indices[best], float(sims[best])


def _common_cluster_phrases(texts: List[str]) -> List[str]:
    return [phrase for phrase, _ in tu.repeated_phrases(texts, n=3, top_k=5)]


def _template_id(text: str) -> str:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
    return f"tmpl_{digest}"


def _deduplicate(
    templates: List[GeneratedTemplate],
    *,
    threshold: float,
    model: EmbeddingModel,
) -> List[GeneratedTemplate]:
    if len(templates) <= 1:
        return templates
    bodies = [t.body_template for t in templates]
    emb = model.encode(bodies)
    keep: List[int] = []
    for i in range(len(templates)):
        is_dup = False
        for j in keep:
            sim = float(emb[i] @ emb[j])
            if sim >= threshold:
                is_dup = True
                # prefer the larger cluster
                if templates[i].cluster_size > templates[j].cluster_size:
                    keep.remove(j)
                    keep.append(i)
                break
        if not is_dup:
            keep.append(i)
    return [templates[i] for i in keep]


def generate_templates(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    clustering: ClusteringResult,
    *,
    settings: Optional[Settings] = None,
    embedding_model: Optional[EmbeddingModel] = None,
) -> List[GeneratedTemplate]:
    """Return a deduplicated list of :class:`GeneratedTemplate` objects.

    Expects ``df`` to already contain ``clean_subject``, ``clean_body``,
    ``combined_text`` and the optional metadata columns. ``embeddings``
    must be in the same order as ``df``.
    """

    settings = settings or get_settings()
    embedding_model = embedding_model or EmbeddingModel(settings=settings)

    if len(df) != embeddings.shape[0]:
        raise ValueError("DataFrame and embeddings must align row-by-row")
    if clustering.centroids is None:
        raise ValueError("Clustering result must include centroids")

    df = df.reset_index(drop=True)
    labels = clustering.labels
    unique_clusters = sorted({int(c) for c in labels if c != -1})

    templates: List[GeneratedTemplate] = []
    cluster_index_map = {c: i for i, c in enumerate(unique_clusters)}

    for cluster_id in unique_clusters:
        member_idx = [i for i, lbl in enumerate(labels) if lbl == cluster_id]
        if not member_idx:
            continue
        centroid = clustering.centroids[cluster_index_map[cluster_id]]
        rep_idx, sim = _representative_index(embeddings, member_idx, centroid)
        rep_row = df.iloc[rep_idx]

        body_template = _build_template_text(str(rep_row.get("clean_body", "")))
        subject_template = _build_subject_template(str(rep_row.get("clean_subject", "")))

        member_subset = df.iloc[member_idx]
        common = _common_cluster_phrases(member_subset["combined_text"].tolist())

        category = _majority_label(member_subset.get("category", pd.Series(dtype=object)).tolist())
        tone = _majority_label(member_subset.get("tone", pd.Series(dtype=object)).tolist()) or _majority_label(
            member_subset.get("formality", pd.Series(dtype=object)).tolist()
        )
        sentiment = _majority_label(member_subset.get("sentiment", pd.Series(dtype=object)).tolist())
        intent = _majority_label(member_subset.get("intent", pd.Series(dtype=object)).tolist())

        templates.append(
            GeneratedTemplate(
                template_id=_template_id(body_template),
                cluster_id=int(cluster_id),
                cluster_size=len(member_idx),
                category=category,
                tone=tone,
                sentiment=sentiment,
                intent=intent,
                subject_template=subject_template,
                body_template=body_template,
                placeholders=_summarise_placeholder_targets(body_template),
                representative_email_id=str(rep_row.get("email_id", "")) or None,
                similarity_to_centroid=sim,
                common_phrases=common,
            )
        )

    # Sort by cluster_size descending so the highest-coverage templates win on tie.
    templates.sort(key=lambda t: t.cluster_size, reverse=True)
    deduped = _deduplicate(
        templates,
        threshold=settings.duplicate_similarity_threshold,
        model=embedding_model,
    )
    if len(deduped) > settings.max_templates:
        deduped = deduped[: settings.max_templates]

    logger.info(
        "Generated %d templates (deduped from %d) across %d clusters",
        len(deduped),
        len(templates),
        clustering.n_clusters,
    )
    return deduped


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
def save_templates(
    templates: List[GeneratedTemplate],
    *,
    settings: Optional[Settings] = None,
) -> Dict[str, Path]:
    """Persist templates to CSV, JSON, and Markdown. Returns the paths."""

    settings = settings or get_settings()
    settings.outputs_dir.mkdir(parents=True, exist_ok=True)

    csv_path = settings.outputs_dir / "templates.csv"
    json_path = settings.outputs_dir / "templates.json"
    md_path = settings.outputs_dir / "templates.md"

    rows = [t.to_dict() for t in templates]
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    write_json(json_path, rows)
    md_path.write_text(_render_markdown(templates), encoding="utf-8")

    return {"csv": csv_path, "json": json_path, "md": md_path}


def _render_markdown(templates: List[GeneratedTemplate]) -> str:
    lines: List[str] = ["# Email Templates", ""]
    for tpl in templates:
        lines.append(f"## {tpl.template_id}")
        meta_bits = [
            f"cluster_id={tpl.cluster_id}",
            f"cluster_size={tpl.cluster_size}",
        ]
        if tpl.category:
            meta_bits.append(f"category={tpl.category}")
        if tpl.tone:
            meta_bits.append(f"tone={tpl.tone}")
        if tpl.sentiment:
            meta_bits.append(f"sentiment={tpl.sentiment}")
        if tpl.intent:
            meta_bits.append(f"intent={tpl.intent}")
        lines.append("- " + " | ".join(meta_bits))
        lines.append("")
        lines.append(f"**Subject:** {tpl.subject_template}")
        lines.append("")
        lines.append("**Body:**")
        lines.append("")
        lines.append("```")
        lines.append(tpl.body_template)
        lines.append("```")
        if tpl.placeholders:
            lines.append("")
            lines.append("**Placeholders:** " + ", ".join(f"`{{{p}}}`" for p in tpl.placeholders))
        if tpl.common_phrases:
            lines.append("")
            lines.append("**Common phrases:** " + ", ".join(tpl.common_phrases))
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)
