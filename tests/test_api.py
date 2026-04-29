"""HTTP-level tests against the FastAPI app."""

from __future__ import annotations

import io

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.main import create_app


@pytest.fixture
def client(monkeypatch, tmp_path, deterministic_embedder):
    from backend.config import get_settings
    from backend.core.pipeline import get_state

    settings = get_settings()
    monkeypatch.setattr(settings, "raw_data_dir", tmp_path / "raw")
    monkeypatch.setattr(settings, "processed_data_dir", tmp_path / "processed")
    monkeypatch.setattr(settings, "outputs_dir", tmp_path / "outputs")
    monkeypatch.setattr(settings, "embedding_cache_file", tmp_path / "emb.npy")
    settings.ensure_directories()

    state = get_state()
    state.artifacts = None
    state.last_uploaded_csv = None

    app = create_app()
    return TestClient(app)


def _csv_bytes(rows: int = 60) -> bytes:
    data = []
    for i in range(rows):
        cat = ["meeting_request", "complaint", "thank_you"][i % 3]
        body_map = {
            "meeting_request": "Hi Alex,\n\nCan we schedule the roadmap call next week?\n\nThanks,\nJamie",
            "complaint": "Dear Support,\n\nIssue with the billing discrepancy.\n\nRegards,\nPat",
            "thank_you": "Hi Maya,\n\nThanks so much for your help with the launch!\n\nWarm regards,\nDrew",
        }
        data.append(
            {
                "email_id": f"E{i:03d}",
                "subject": f"Subject {i}",
                "body": body_map[cat],
                "category": cat,
                "tone": "formal",
                "sentiment": "neutral",
                "sender": "Jamie",
                "recipient": "Alex",
                "created_at": "2024-05-01",
            }
        )
    df = pd.DataFrame(data)
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def test_health_returns_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    payload = r.json()
    assert payload["status"] == "ok"
    assert "version" in payload


def test_upload_validates_extension(client):
    r = client.post(
        "/api/upload",
        files={"file": ("bad.txt", b"hello", "text/plain")},
    )
    assert r.status_code == 400


def test_upload_then_run_pipeline_then_endpoints(client):
    # Upload
    r = client.post(
        "/api/upload",
        files={"file": ("emails.csv", _csv_bytes(), "text/csv")},
    )
    assert r.status_code == 201, r.text

    # Run pipeline
    r = client.post("/api/run-pipeline", json={"clustering_method": "kmeans", "n_clusters": 3})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "completed"
    assert body["n_emails"] > 0
    assert body["n_templates"] >= 1

    # Templates list
    r = client.get("/api/templates")
    assert r.status_code == 200
    templates = r.json()["templates"]
    assert len(templates) >= 1
    template_id = templates[0]["template_id"]

    # Single template
    r = client.get(f"/api/templates/{template_id}")
    assert r.status_code == 200
    assert r.json()["template_id"] == template_id

    # 404 path
    r = client.get("/api/templates/does-not-exist")
    assert r.status_code == 404

    # Evaluation
    r = client.get("/api/evaluation")
    assert r.status_code == 200
    metrics = r.json()
    assert "n_clusters" in metrics

    # Output downloads
    r = client.get("/api/outputs/markdown")
    assert r.status_code == 200
    assert "Email Templates" in r.text

    # Generate-template
    r = client.post(
        "/api/generate-template",
        json={"subject": "Need a meeting", "body": "Hi Sam, can we sync about the roadmap?"},
    )
    assert r.status_code == 200
    payload = r.json()
    assert len(payload["matches"]) >= 1
    assert payload["matches"][0]["similarity"] >= 0


def test_get_templates_without_pipeline_returns_409(client):
    r = client.get("/api/templates")
    assert r.status_code == 409
