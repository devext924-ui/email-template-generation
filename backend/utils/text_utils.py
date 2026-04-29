"""Reusable text helpers shared by preprocessing and template generation.

These functions are deliberately dependency-free (regex + stdlib) so they
remain fast and trivially unit-testable.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Iterable, List, Tuple


_GREETING_PATTERNS = [
    r"^\s*(hi|hello|hey|dear|greetings|good\s+(morning|afternoon|evening))\b[^\n]*",
]
_CLOSING_PATTERNS = [
    r"\b(best|kind|warm|sincere)\s+(regards|wishes)\b[^\n]*",
    r"\b(regards|cheers|thanks|thank\s+you|thanks\s+a\s+lot|sincerely|respectfully)\b[^\n]*",
    r"\b(yours\s+truly|yours\s+faithfully|talk\s+soon)\b[^\n]*",
]

_SIGNATURE_HINTS = [
    r"^--\s*$",
    r"^\s*sent\s+from\s+my\s+\w+",
    r"^\s*get\s+outlook\s+for\s+\w+",
    r"^\s*confidentiality\s+notice",
    r"^\s*this\s+email\s+(and\s+any\s+attachments\s+)?is\s+confidential",
    r"^\s*disclaimer\s*:",
]

_QUOTE_PATTERNS = [
    r"^\s*on\s+\w+,\s+\w+\s+\d+,\s+\d{4}.*?wrote:\s*$",
    r"^\s*from:\s+.*$",
    r"^\s*sent:\s+.*$",
    r"^\s*to:\s+.*$",
    r"^\s*subject:\s+.*$",
    r"^\s*-+\s*original\s+message\s*-+",
    r"^\s*>.*$",
]

_TRACKING_PATTERNS = [
    r"https?://(?:[^\s]+?(?:track|click|utm_|mailtrack|sendgrid|mailchimp)[^\s]*)",
    r"\[image:[^\]]+\]",
    r"unsubscribe\s+here.*$",
]

_PLACEHOLDER_HINTS = {
    "recipient_name": [r"\b(dear|hi|hello|hey)\s+([A-Z][a-z]+)\b"],
    "sender_name": [r"\b(regards|sincerely|thanks),?\s+\n?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"],
    "company_name": [r"\b(at|from|of)\s+([A-Z][A-Za-z&\.\s]{2,30}(?:Inc|LLC|Ltd|Corp|Co\.))\b"],
    "date": [
        r"\b(?:on\s+)?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
        r"\b(?:on\s+)?(\w+\s+\d{1,2},?\s+\d{4})\b",
        r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
    ],
    "deadline": [r"\bby\s+(end\s+of\s+\w+|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+\s+\d{1,2})\b"],
}

_ACTION_KEYWORDS = {
    "review",
    "approve",
    "confirm",
    "schedule",
    "reschedule",
    "send",
    "share",
    "submit",
    "complete",
    "update",
    "follow up",
    "respond",
    "reply",
    "join",
    "attend",
    "sign",
    "pay",
    "invoice",
    "deliver",
    "ship",
    "ship out",
    "investigate",
    "resolve",
    "escalate",
    "verify",
    "check",
}


def normalize_whitespace(text: str) -> str:
    """Collapse runs of whitespace and trim borders without dropping line structure."""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def remove_quoted_replies(text: str) -> str:
    """Strip forwarded/quoted reply chains from a multi-line email."""

    lines = text.split("\n")
    cleaned: List[str] = []
    in_quote_block = False
    for line in lines:
        lowered = line.lower()
        if any(re.match(pat, lowered) for pat in _QUOTE_PATTERNS):
            in_quote_block = True
            continue
        if in_quote_block and (lowered.strip() == "" or lowered.lstrip().startswith(">")):
            continue
        in_quote_block = False
        cleaned.append(line)
    return "\n".join(cleaned)


def remove_signatures(text: str) -> str:
    """Drop trailing signature blocks based on common heuristics."""

    lines = text.split("\n")
    cutoff = len(lines)
    for i, raw in enumerate(lines):
        line = raw.strip().lower()
        if any(re.search(p, line) for p in _SIGNATURE_HINTS):
            cutoff = i
            break
    return "\n".join(lines[:cutoff]).rstrip()


def remove_tracking_text(text: str) -> str:
    """Remove tracking links, image placeholders, and unsubscribe footers."""

    out = text
    for pattern in _TRACKING_PATTERNS:
        out = re.sub(pattern, "", out, flags=re.IGNORECASE)
    return out


def extract_greeting(text: str) -> str:
    """Return the first greeting line if it matches a known pattern."""

    for line in text.split("\n"):
        candidate = line.strip()
        if not candidate:
            continue
        for pattern in _GREETING_PATTERNS:
            if re.match(pattern, candidate, flags=re.IGNORECASE):
                return candidate
        return ""
    return ""


def extract_closing(text: str) -> str:
    """Return the closing line if a known closing keyword is present near the end."""

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    for line in reversed(lines[-6:] if len(lines) > 6 else lines):
        for pattern in _CLOSING_PATTERNS:
            if re.search(pattern, line, flags=re.IGNORECASE):
                return line
    return ""


def normalize_greeting(text: str) -> str:
    """Replace the detected greeting with a canonical placeholder line."""

    greeting = extract_greeting(text)
    if not greeting:
        return text
    return text.replace(greeting, "Hi {recipient_name},", 1)


def normalize_closing(text: str) -> str:
    """Replace the detected closing block with a canonical signoff."""

    closing = extract_closing(text)
    if not closing:
        return text
    return text.replace(closing, "Best regards,\n{sender_name}", 1)


def detect_action_words(text: str) -> List[str]:
    """Return action verbs found in the email body."""

    lowered = text.lower()
    found = sorted({word for word in _ACTION_KEYWORDS if word in lowered})
    return found


def detect_placeholders(text: str) -> List[str]:
    """Return the set of placeholder slot names that the email could expose."""

    placeholders: List[str] = []
    for slot, patterns in _PLACEHOLDER_HINTS.items():
        for pattern in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                placeholders.append(slot)
                break
    return placeholders


def detect_intent(text: str) -> str:
    """Return a coarse intent label using keyword matching."""

    lowered = text.lower()
    rules = [
        ("complaint", ["complain", "unacceptable", "frustrated", "unhappy", "issue with"]),
        ("apology", ["apologi", "sorry for", "regret"]),
        ("confirmation", ["confirm", "confirmation", "received", "acknowledge"]),
        ("follow_up", ["follow up", "following up", "checking in", "any update"]),
        ("request", ["could you", "would you", "please", "request", "kindly"]),
        ("scheduling", ["meeting", "calendar", "schedule", "reschedule", "availability"]),
        ("invoice", ["invoice", "payment", "billing", "amount due"]),
        ("introduction", ["introduce", "introduction", "nice to meet"]),
        ("announcement", ["announcement", "we are excited", "pleased to announce"]),
        ("thank_you", ["thank you", "thanks for", "appreciate"]),
    ]
    for label, keywords in rules:
        if any(k in lowered for k in keywords):
            return label
    return "general"


def detect_formality(text: str) -> str:
    """Return a coarse formality label: formal, neutral, casual."""

    casual_markers = ("hey ", "yo ", "thx", "cheers", "lol", "btw", "asap")
    formal_markers = (
        "dear",
        "sincerely",
        "kind regards",
        "respectfully",
        "to whom it may concern",
        "yours faithfully",
    )
    lowered = text.lower()
    if any(m in lowered for m in formal_markers):
        return "formal"
    if any(m in lowered for m in casual_markers):
        return "casual"
    return "neutral"


def repeated_phrases(texts: Iterable[str], n: int = 3, top_k: int = 10) -> List[Tuple[str, int]]:
    """Return the top-k n-grams shared across a corpus of texts."""

    counter: Counter[str] = Counter()
    for text in texts:
        tokens = re.findall(r"[A-Za-z']+", text.lower())
        for i in range(len(tokens) - n + 1):
            counter[" ".join(tokens[i : i + n])] += 1
    return counter.most_common(top_k)


def build_combined_text(subject: str, body: str) -> str:
    """Combine subject and body into a single training/embedding string."""

    subject = (subject or "").strip()
    body = (body or "").strip()
    if subject and body:
        return f"{subject}\n\n{body}"
    return subject or body
