"""Tests for backend.core.data_loader."""

from __future__ import annotations

import pandas as pd
import pytest

from backend.core.data_loader import (
    DataValidationError,
    clean_dataframe,
    generate_sample_dataset,
    load_csv,
    normalize_columns,
    validate_columns,
)


def test_normalize_columns_lowercases_and_snake_cases():
    df = pd.DataFrame(columns=["Email ID", "Subject", "Body Text", "Sent-At"])
    out = normalize_columns(df)
    assert list(out.columns) == ["email_id", "subject", "body_text", "sent_at"]


def test_validate_columns_passes_when_all_present():
    df = pd.DataFrame(columns=["email_id", "subject", "body"])
    validate_columns(df)


def test_validate_columns_raises_on_missing():
    df = pd.DataFrame(columns=["email_id", "subject"])
    with pytest.raises(DataValidationError):
        validate_columns(df)


def test_clean_dataframe_drops_empty_bodies_and_fills_optionals():
    df = pd.DataFrame(
        {
            "email_id": ["1", "2", "3"],
            "subject": ["Hello", None, "Hi"],
            "body": ["Body 1", "Body 2", ""],
        }
    )
    cleaned = clean_dataframe(df)
    assert len(cleaned) == 2
    for col in ("category", "sentiment", "tone", "sender", "recipient", "created_at"):
        assert col in cleaned.columns


def test_load_csv_round_trip(tmp_path):
    raw = pd.DataFrame(
        {
            "Email ID": ["E1", "E2"],
            "Subject": ["Hi", "Hello"],
            "Body": ["Hi there", "Hello there"],
        }
    )
    csv_path = tmp_path / "raw.csv"
    raw.to_csv(csv_path, index=False)
    df = load_csv(csv_path)
    assert {"email_id", "subject", "body"}.issubset(df.columns)
    assert len(df) == 2


def test_generate_sample_dataset_size_and_columns():
    df = generate_sample_dataset(n=120)
    assert len(df) == 120
    assert {"email_id", "subject", "body", "category", "tone", "sentiment"}.issubset(df.columns)
    assert df["body"].str.len().min() > 0
