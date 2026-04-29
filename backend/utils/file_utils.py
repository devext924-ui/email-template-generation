"""Filesystem helpers for the backend."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def ensure_dir(path: str | Path) -> Path:
    """Create the directory if missing and return the resolved Path."""

    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_json(path: str | Path, data: Any, *, indent: int = 2) -> Path:
    """Write JSON to disk with UTF-8 encoding, returning the path."""

    p = Path(path)
    ensure_dir(p.parent)
    with p.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=indent, default=str)
    return p


def read_json(path: str | Path) -> Any:
    """Load a JSON document from disk."""

    with Path(path).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def safe_filename(name: str) -> str:
    """Replace characters not allowed in common filesystems."""

    keep = "._-"
    return "".join(c if (c.isalnum() or c in keep) else "_" for c in name).strip("_") or "file"
