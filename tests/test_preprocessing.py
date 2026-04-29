"""Tests for backend.core.preprocessing and backend.utils.text_utils."""

from __future__ import annotations

import pandas as pd

from backend.core.preprocessing import (
    clean_email_text,
    extract_features,
    preprocess_dataframe,
)
from backend.utils import text_utils as tu


def test_normalize_whitespace_collapses_runs():
    text = "Hello\r\n\r\n   world  \t  \n\n\n!"
    cleaned = tu.normalize_whitespace(text)
    assert "\r" not in cleaned
    assert "\n\n\n" not in cleaned
    assert "  " not in cleaned  # no double spaces
    assert cleaned.strip() == cleaned  # trimmed at borders


def test_remove_signatures_strips_sent_from_block():
    body = (
        "Hi Alex,\nPlease review the doc.\n\nThanks,\nJamie\n\nSent from my iPhone\n"
        "Confidentiality notice: this email is private."
    )
    cleaned = tu.remove_signatures(body)
    assert "iPhone" not in cleaned
    assert "Confidentiality" not in cleaned
    assert "Please review the doc" in cleaned


def test_remove_quoted_replies_strips_forwarded_chain():
    body = (
        "Hi team,\nQuick update.\n\n"
        "On Tue, Mar 5, 2024 at 10:00 AM, John Doe wrote:\n"
        "> Original message\n"
        "> with multiple lines\n"
    )
    cleaned = tu.remove_quoted_replies(body)
    assert "Original message" not in cleaned
    assert "Quick update" in cleaned


def test_remove_tracking_text_drops_tracking_links():
    text = "Click https://example.com/track?utm_source=email here. [image: logo]"
    cleaned = tu.remove_tracking_text(text)
    assert "track" not in cleaned
    assert "[image:" not in cleaned


def test_extract_greeting_and_closing():
    text = "Hi Alex,\n\nLet's catch up.\n\nBest regards,\nJamie"
    assert "alex" in tu.extract_greeting(text).lower()
    assert "regards" in tu.extract_closing(text).lower()


def test_detect_intent_and_formality():
    apology = "Dear customer, please accept our apologies for the inconvenience."
    request = "Hey, could you please review this when you get a chance?"
    assert tu.detect_intent(apology) == "apology"
    assert tu.detect_formality(apology) == "formal"
    assert tu.detect_intent(request) == "request"
    assert tu.detect_formality(request) in {"casual", "neutral"}


def test_clean_email_text_full_pipeline():
    raw = (
        "Hi Alex,\n\nPlease review the deck.\n\nThanks,\nJamie\n\n"
        "On Mon, Apr 1, 2024 at 9:00 AM, Bot wrote:\n> Old\n> message\n"
        "Sent from my iPhone"
    )
    cleaned = clean_email_text(raw)
    assert "Old" not in cleaned
    assert "iPhone" not in cleaned
    assert "Please review" in cleaned


def test_extract_features_returns_expected_fields():
    text = "Hi Alex,\n\nCould you please confirm the meeting? We need this ASAP.\n\nThanks,\nJamie"
    feats = extract_features(text)
    assert feats.intent in {"confirmation", "request", "scheduling"}
    assert "confirm" in feats.action_words or "confirm" in text.lower()


def test_preprocess_dataframe_adds_columns(tiny_dataframe):
    df = preprocess_dataframe(tiny_dataframe)
    for col in ("clean_subject", "clean_body", "combined_text", "intent", "formality"):
        assert col in df.columns
    assert df["combined_text"].str.len().gt(0).all()
