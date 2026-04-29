"""CSV loading, validation, and sample dataset generation.

This module is the entry point for getting an email dataset into the
pipeline. It is tolerant of messy real-world CSVs (extra columns, mixed
casing, missing optional fields) but strict about the required schema.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd

from backend.config import get_settings
from backend.logging_config import get_logger

logger = get_logger(__name__)

REQUIRED_COLUMNS: List[str] = ["email_id", "subject", "body"]
OPTIONAL_COLUMNS: List[str] = [
    "category",
    "sentiment",
    "tone",
    "sender",
    "recipient",
    "created_at",
]


class DataValidationError(ValueError):
    """Raised when the input CSV cannot be safely turned into the canonical schema."""


def _normalize_column_name(col: str) -> str:
    return col.strip().lower().replace(" ", "_").replace("-", "_")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of ``df`` with columns lower-cased and snake_cased."""

    df = df.copy()
    df.columns = [_normalize_column_name(c) for c in df.columns]
    return df


def validate_columns(df: pd.DataFrame, required: Iterable[str] = REQUIRED_COLUMNS) -> None:
    """Raise DataValidationError if any required columns are missing."""

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise DataValidationError(
            f"Missing required columns: {missing}. Found columns: {list(df.columns)}"
        )


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows missing critical fields and coerce types to expected dtypes."""

    df = df.copy()
    df = df.dropna(subset=["body"]).reset_index(drop=True)
    df["subject"] = df.get("subject", "").fillna("").astype(str)
    df["body"] = df["body"].fillna("").astype(str)
    df["email_id"] = df["email_id"].astype(str)

    for col in OPTIONAL_COLUMNS:
        if col not in df.columns:
            df[col] = None

    df["body"] = df["body"].str.strip()
    df["subject"] = df["subject"].str.strip()
    df = df[df["body"].str.len() > 0].reset_index(drop=True)
    return df


def load_csv(path: str | Path) -> pd.DataFrame:
    """Load a CSV file into a normalized, validated DataFrame."""

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    df = pd.read_csv(path)
    df = normalize_columns(df)
    validate_columns(df)
    df = clean_dataframe(df)
    logger.info("Loaded %d rows from %s", len(df), path)
    return df


def save_processed(df: pd.DataFrame, name: str = "cleaned_emails.csv") -> Path:
    """Persist the cleaned dataset to ``data/processed/<name>``."""

    settings = get_settings()
    out_path = settings.processed_data_dir / name
    df.to_csv(out_path, index=False)
    logger.info("Saved processed dataset to %s", out_path)
    return out_path


def ensure_dataset(path: Optional[str | Path] = None) -> pd.DataFrame:
    """Return a usable dataset.

    Resolution order:
    1. Explicit ``path`` argument.
    2. The configured sample CSV if it exists on disk.
    3. A freshly generated synthetic dataset (also written to disk).
    """

    settings = get_settings()
    if path is not None:
        return load_csv(path)

    if settings.sample_csv.exists():
        return load_csv(settings.sample_csv)

    logger.warning("Sample dataset missing; generating a synthetic one at %s", settings.sample_csv)
    df = generate_sample_dataset()
    settings.sample_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(settings.sample_csv, index=False)
    return df


# ---------------------------------------------------------------------------
# Synthetic dataset generation
# ---------------------------------------------------------------------------

_TEMPLATE_BANK: List[dict] = [
    {
        "category": "meeting_request",
        "tone": "formal",
        "sentiment": "neutral",
        "subjects": [
            "Meeting request for {topic}",
            "Quick sync on {topic}",
            "Can we schedule a call about {topic}?",
        ],
        "bodies": [
            (
                "Hi {recipient},\n\nI hope you're doing well. Could we schedule a meeting next week to discuss {topic}? "
                "I'm flexible on timing — please share a few slots that work for you.\n\nBest regards,\n{sender}"
            ),
            (
                "Hello {recipient},\n\nI'd love to set up a 30 minute call to align on {topic}. Are you available {date} or later in the week?\n\n"
                "Thanks,\n{sender}"
            ),
        ],
    },
    {
        "category": "follow_up",
        "tone": "neutral",
        "sentiment": "neutral",
        "subjects": [
            "Following up on {topic}",
            "Quick follow-up regarding {topic}",
            "Checking in on {topic}",
        ],
        "bodies": [
            (
                "Hi {recipient},\n\nJust circling back on {topic}. Did you get a chance to review the materials I sent over? "
                "Happy to jump on a call if it's easier.\n\nThanks,\n{sender}"
            ),
            (
                "Hello {recipient},\n\nFollowing up on my previous email about {topic}. Could you share an update by {deadline}?\n\nBest,\n{sender}"
            ),
        ],
    },
    {
        "category": "complaint",
        "tone": "formal",
        "sentiment": "negative",
        "subjects": [
            "Issue with {topic}",
            "Complaint regarding {topic}",
            "Unacceptable experience with {topic}",
        ],
        "bodies": [
            (
                "Dear {recipient},\n\nI'm writing to express my frustration with {issue}. This has caused significant disruption "
                "and I would appreciate a prompt response on how you intend to resolve this.\n\nRegards,\n{sender}"
            ),
            (
                "Hello {recipient},\n\nI am very unhappy with the recent {topic}. The {issue} is unacceptable. "
                "Please investigate and respond by {deadline}.\n\nSincerely,\n{sender}"
            ),
        ],
    },
    {
        "category": "apology",
        "tone": "formal",
        "sentiment": "negative",
        "subjects": [
            "Our apologies regarding {topic}",
            "We're sorry about {issue}",
            "Apology for {issue}",
        ],
        "bodies": [
            (
                "Dear {recipient},\n\nPlease accept our sincere apologies for the {issue}. We are taking immediate steps to "
                "ensure this does not happen again. As a goodwill gesture, we'd like to offer {action_required}.\n\nKind regards,\n{sender}"
            ),
            (
                "Hi {recipient},\n\nI'm truly sorry for the inconvenience caused by {issue}. We've identified the root cause and "
                "are working on a fix. I'll keep you updated.\n\nBest,\n{sender}"
            ),
        ],
    },
    {
        "category": "thank_you",
        "tone": "neutral",
        "sentiment": "positive",
        "subjects": [
            "Thank you for {topic}",
            "Appreciate your help with {topic}",
            "Thanks for the {topic}",
        ],
        "bodies": [
            (
                "Hi {recipient},\n\nThank you so much for {topic}. Your support meant a lot and made a real difference.\n\n"
                "Warm regards,\n{sender}"
            ),
            (
                "Hello {recipient},\n\nI really appreciate your help with {topic}. Looking forward to working together again.\n\nThanks,\n{sender}"
            ),
        ],
    },
    {
        "category": "invoice",
        "tone": "formal",
        "sentiment": "neutral",
        "subjects": [
            "Invoice {invoice_no} for {topic}",
            "Payment due for {topic}",
            "Outstanding invoice {invoice_no}",
        ],
        "bodies": [
            (
                "Dear {recipient},\n\nPlease find attached invoice {invoice_no} for {topic}. The amount due is payable by {deadline}. "
                "Let me know if you have any questions.\n\nRegards,\n{sender}"
            ),
            (
                "Hello {recipient},\n\nThis is a friendly reminder that invoice {invoice_no} is outstanding. "
                "Could you process payment by {deadline}?\n\nThanks,\n{sender}"
            ),
        ],
    },
    {
        "category": "introduction",
        "tone": "neutral",
        "sentiment": "positive",
        "subjects": [
            "Introducing {sender}",
            "Quick introduction — {topic}",
            "Hello from {sender}",
        ],
        "bodies": [
            (
                "Hi {recipient},\n\nMy name is {sender} and I'm reaching out about {topic}. I'd love to learn more about your work "
                "and explore potential collaboration.\n\nBest,\n{sender}"
            ),
            (
                "Hello {recipient},\n\nI'm {sender}, the new {role} at {company}. I'm excited to connect and discuss {topic}.\n\n"
                "Looking forward,\n{sender}"
            ),
        ],
    },
    {
        "category": "confirmation",
        "tone": "neutral",
        "sentiment": "positive",
        "subjects": [
            "Confirmation: {topic}",
            "Confirmed — {topic}",
            "Your {topic} is confirmed",
        ],
        "bodies": [
            (
                "Hi {recipient},\n\nThis email confirms that {topic} is scheduled for {date}. Please let me know if anything changes.\n\n"
                "Thanks,\n{sender}"
            ),
            (
                "Hello {recipient},\n\nYour request for {topic} has been received and confirmed. Reference number: {invoice_no}.\n\nRegards,\n{sender}"
            ),
        ],
    },
    {
        "category": "announcement",
        "tone": "formal",
        "sentiment": "positive",
        "subjects": [
            "Exciting news about {topic}",
            "Announcement: {topic}",
            "Update on {topic}",
        ],
        "bodies": [
            (
                "Dear {recipient},\n\nWe are pleased to announce {topic}. This will help us {action_required}. "
                "More details to follow soon.\n\nBest regards,\n{sender}"
            ),
            (
                "Hi {recipient},\n\nQuick announcement — {topic} goes live on {date}. We'll share follow-up materials shortly.\n\nThanks,\n{sender}"
            ),
        ],
    },
    {
        "category": "urgent_request",
        "tone": "formal",
        "sentiment": "negative",
        "subjects": [
            "URGENT: {topic}",
            "Time-sensitive: {topic}",
            "Action required by {deadline}",
        ],
        "bodies": [
            (
                "Hi {recipient},\n\nThis is urgent — could you please {action_required} regarding {topic} by {deadline}? "
                "Let me know if you anticipate any blockers.\n\nThanks,\n{sender}"
            ),
            (
                "Dear {recipient},\n\nWe need your immediate attention on {issue}. Please {action_required} as soon as possible.\n\nRegards,\n{sender}"
            ),
        ],
    },
]

_FILLERS = {
    "topic": [
        "the Q3 roadmap",
        "the marketing campaign",
        "the new pricing plan",
        "the customer onboarding flow",
        "the product launch",
        "the partnership agreement",
        "the security audit",
        "the analytics dashboard",
        "the hiring pipeline",
        "the migration project",
    ],
    "issue": [
        "delayed delivery",
        "billing discrepancy",
        "outage on our staging environment",
        "missing line items",
        "inaccurate invoice",
        "downtime",
        "communication gap",
    ],
    "action_required": [
        "expedite the shipment",
        "issue a refund",
        "approve the change request",
        "share the latest mockups",
        "process the payment",
        "merge the pull request",
        "update the roadmap",
    ],
    "deadline": ["EOD Friday", "next Monday", "October 15", "the end of the week", "tomorrow"],
    "date": ["Tuesday", "next Wednesday", "July 22", "next quarter", "tomorrow afternoon"],
    "recipient": ["Alex", "Jordan", "Taylor", "Morgan", "Sam", "Priya", "Diego", "Maya", "Chris"],
    "sender": ["Jamie", "Riley", "Pat", "Cameron", "Drew", "Ananya", "Marco", "Lina"],
    "company": ["Acme Corp", "Globex", "Initech", "Umbrella Inc", "Hooli", "Wayne Enterprises"],
    "role": ["account manager", "engineering lead", "product manager", "customer success lead"],
    "invoice_no": [f"INV-{i:05d}" for i in range(1000, 1100)],
}


def generate_sample_dataset(n: int = 1100, seed: int = 17) -> pd.DataFrame:
    """Generate a synthetic but realistic email corpus.

    The dataset is large enough (>=1000 rows) for clustering experiments and
    spans the categories defined in :data:`_TEMPLATE_BANK`.
    """

    rng = random.Random(seed)
    rows: List[dict] = []
    for i in range(n):
        spec = rng.choice(_TEMPLATE_BANK)
        subject = rng.choice(spec["subjects"])
        body = rng.choice(spec["bodies"])
        fillers = {k: rng.choice(v) for k, v in _FILLERS.items()}
        try:
            subject_filled = subject.format(**fillers)
            body_filled = body.format(**fillers)
        except KeyError:
            subject_filled = subject
            body_filled = body

        rows.append(
            {
                "email_id": f"E{i:05d}",
                "subject": subject_filled,
                "body": body_filled,
                "category": spec["category"],
                "tone": spec["tone"],
                "sentiment": spec["sentiment"],
                "sender": fillers["sender"],
                "recipient": fillers["recipient"],
                "created_at": pd.Timestamp("2024-01-01") + pd.Timedelta(days=rng.randint(0, 365)),
            }
        )

    df = pd.DataFrame(rows)
    return df
