"""Email preprocessing pipeline.

Transforms each email row into a clean, normalized text representation
plus a small feature dictionary used downstream for template generation
and weak supervision.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import pandas as pd

from backend.logging_config import get_logger
from backend.utils import text_utils as tu

logger = get_logger(__name__)


@dataclass
class EmailFeatures:
    greeting: str
    closing: str
    intent: str
    formality: str
    placeholders: List[str]
    action_words: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "greeting": self.greeting,
            "closing": self.closing,
            "intent": self.intent,
            "formality": self.formality,
            "placeholders": self.placeholders,
            "action_words": self.action_words,
        }


def clean_email_text(text: str) -> str:
    """Apply the full preprocessing chain to a single email body."""

    text = tu.normalize_whitespace(text)
    text = tu.remove_quoted_replies(text)
    text = tu.remove_signatures(text)
    text = tu.remove_tracking_text(text)
    text = tu.normalize_whitespace(text)
    return text


def extract_features(text: str) -> EmailFeatures:
    """Return a small feature record describing the email."""

    return EmailFeatures(
        greeting=tu.extract_greeting(text),
        closing=tu.extract_closing(text),
        intent=tu.detect_intent(text),
        formality=tu.detect_formality(text),
        placeholders=tu.detect_placeholders(text),
        action_words=tu.detect_action_words(text),
    )


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Add cleaned text, combined text, and extracted features to ``df``.

    Adds columns:
        - clean_body
        - clean_subject
        - combined_text
        - features (dict)
        - intent, formality (flattened for convenience)
    """

    df = df.copy()
    df["clean_subject"] = df["subject"].fillna("").astype(str).map(tu.normalize_whitespace)
    df["clean_body"] = df["body"].fillna("").astype(str).map(clean_email_text)
    df["combined_text"] = [
        tu.build_combined_text(s, b) for s, b in zip(df["clean_subject"], df["clean_body"])
    ]

    feats = [extract_features(t) for t in df["combined_text"]]
    df["features"] = [f.to_dict() for f in feats]
    df["intent"] = [f.intent for f in feats]
    df["formality"] = [f.formality for f in feats]
    df["greeting"] = [f.greeting for f in feats]
    df["closing"] = [f.closing for f in feats]

    logger.info("Preprocessed %d emails", len(df))
    return df
