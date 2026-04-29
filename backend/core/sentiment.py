"""Sentiment, tone, and intent detection.

Two backends are supported:
- ``rule_based`` (default): deterministic, dependency-free, fast.
- ``transformer``: optional Hugging Face pipeline for higher accuracy.

The transformer backend is loaded lazily and falls back to the rule-based
classifier on import or runtime errors so the pipeline never breaks if
the optional model is missing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from backend.config import Settings, get_settings
from backend.logging_config import get_logger

logger = get_logger(__name__)


SENTIMENT_LABELS = ("positive", "neutral", "negative")
TONE_LABELS = (
    "formal",
    "casual",
    "neutral",
    "urgent",
    "apologetic",
    "persuasive",
    "follow_up",
    "complaint",
    "request",
    "confirmation",
)


@dataclass
class SentimentResult:
    sentiment: str
    tone: str
    scores: Dict[str, float]


_POSITIVE_WORDS = {
    "thanks",
    "thank you",
    "appreciate",
    "grateful",
    "great",
    "excellent",
    "wonderful",
    "love",
    "excited",
    "happy",
    "pleased",
    "amazing",
    "perfect",
    "fantastic",
    "looking forward",
}
_NEGATIVE_WORDS = {
    "unhappy",
    "frustrated",
    "disappointed",
    "angry",
    "upset",
    "bad",
    "terrible",
    "awful",
    "unacceptable",
    "issue",
    "problem",
    "delay",
    "broken",
    "complaint",
    "sorry",
    "apolog",
    "mistake",
    "fail",
}
_URGENT_WORDS = {"urgent", "asap", "immediately", "critical", "today", "deadline", "time-sensitive"}
_PERSUASIVE_WORDS = {"recommend", "suggest", "consider", "believe", "convince", "imagine"}
_REQUEST_MARKERS = {"could you", "would you", "please", "kindly", "request"}
_FOLLOWUP_MARKERS = {"follow up", "following up", "circling back", "checking in", "any update"}
_CONFIRMATION_MARKERS = {"confirm", "confirmation", "acknowledge", "received"}
_COMPLAINT_MARKERS = {"complaint", "complain", "unacceptable", "frustrat", "issue with"}
_APOLOGY_MARKERS = {"apolog", "sorry for", "regret"}
_FORMAL_MARKERS = {"dear", "sincerely", "regards", "respectfully", "to whom it may concern"}
_CASUAL_MARKERS = {"hey", "yo ", "thx", "cheers", "lol", "btw"}


def _count_hits(text: str, markers) -> int:
    return sum(1 for m in markers if m in text)


def rule_based_sentiment(text: str) -> SentimentResult:
    """Dependency-free sentiment & tone classifier."""

    lowered = text.lower()
    pos = _count_hits(lowered, _POSITIVE_WORDS)
    neg = _count_hits(lowered, _NEGATIVE_WORDS)
    if pos > neg:
        sentiment = "positive"
    elif neg > pos:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    tone_scores = {
        "urgent": _count_hits(lowered, _URGENT_WORDS),
        "apologetic": _count_hits(lowered, _APOLOGY_MARKERS),
        "complaint": _count_hits(lowered, _COMPLAINT_MARKERS),
        "follow_up": _count_hits(lowered, _FOLLOWUP_MARKERS),
        "confirmation": _count_hits(lowered, _CONFIRMATION_MARKERS),
        "request": _count_hits(lowered, _REQUEST_MARKERS),
        "persuasive": _count_hits(lowered, _PERSUASIVE_WORDS),
        "formal": _count_hits(lowered, _FORMAL_MARKERS),
        "casual": _count_hits(lowered, _CASUAL_MARKERS),
    }
    if max(tone_scores.values()) == 0:
        tone = "neutral"
    else:
        tone = max(tone_scores, key=tone_scores.get)

    return SentimentResult(
        sentiment=sentiment,
        tone=tone,
        scores={
            "positive": float(pos),
            "negative": float(neg),
            **{k: float(v) for k, v in tone_scores.items()},
        },
    )


class SentimentAnalyzer:
    """Adapter that routes to the configured backend."""

    def __init__(self, backend: Optional[str] = None, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.backend = backend or self.settings.sentiment_backend
        self._pipeline = None
        if self.backend == "transformer":
            try:
                from transformers import pipeline  # lazy import

                self._pipeline = pipeline(
                    "sentiment-analysis",
                    model="distilbert-base-uncased-finetuned-sst-2-english",
                )
                logger.info("Loaded transformer sentiment pipeline")
            except Exception as exc:  # pragma: no cover - optional
                logger.warning("Falling back to rule-based sentiment: %s", exc)
                self.backend = "rule_based"
                self._pipeline = None

    def analyze(self, text: str) -> SentimentResult:
        if self.backend == "transformer" and self._pipeline is not None:
            try:
                out = self._pipeline(text[:512])[0]
                label = out["label"].lower()
                score = float(out["score"])
                sentiment = "positive" if "pos" in label else "negative" if "neg" in label else "neutral"
                base = rule_based_sentiment(text)
                return SentimentResult(
                    sentiment=sentiment,
                    tone=base.tone,
                    scores={**base.scores, "transformer_confidence": score},
                )
            except Exception as exc:  # pragma: no cover
                logger.warning("Transformer sentiment failed; using rule-based: %s", exc)
        return rule_based_sentiment(text)

    def analyze_many(self, texts: List[str]) -> List[SentimentResult]:
        return [self.analyze(t) for t in texts]
