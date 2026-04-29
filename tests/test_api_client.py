"""Tests for the shared frontend API client."""

from __future__ import annotations

import httpx
import pytest

from frontend.api_client import ApiClientError, EmailTemplateApiClient


def test_api_client_sends_pipeline_payload():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "status": "completed",
                "n_emails": 10,
                "n_clusters": 3,
                "n_templates": 3,
                "evaluation": {},
                "templates_csv": "outputs/templates.csv",
                "templates_json": "outputs/templates.json",
                "templates_md": "outputs/templates.md",
                "duration_seconds": 1.2,
            },
        )

    client = EmailTemplateApiClient(
        "http://testserver",
        transport=httpx.MockTransport(handler),
    )
    result = client.run_pipeline(csv_path="data/raw/emails.csv", n_clusters=3)

    assert result["status"] == "completed"
    assert requests[0].url.path == "/api/run-pipeline"
    assert requests[0].method == "POST"
    assert requests[0].read() == b'{"csv_path":"data/raw/emails.csv","n_clusters":3}'


def test_api_client_uploads_csv_as_multipart():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/upload"
        assert "multipart/form-data" in request.headers["content-type"]
        assert b"email_id,subject,body" in request.read()
        return httpx.Response(
            201,
            json={
                "filename": "emails.csv",
                "rows": 1,
                "columns": ["email_id", "subject", "body"],
                "saved_path": "data/raw/emails.csv",
                "message": "ok",
            },
        )

    client = EmailTemplateApiClient(
        "http://testserver",
        transport=httpx.MockTransport(handler),
    )

    result = client.upload_csv("emails.csv", b"email_id,subject,body\n1,A,B\n")
    assert result["rows"] == 1


def test_api_client_raises_clean_backend_errors():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(409, json={"detail": "Pipeline has not been run yet."})

    client = EmailTemplateApiClient(
        "http://testserver",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ApiClientError, match="Pipeline has not been run yet") as exc:
        client.list_templates()

    assert exc.value.status_code == 409


def test_api_client_download_output_metadata():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=b"# Email Templates\n",
            headers={
                "content-disposition": 'attachment; filename="templates.md"',
                "content-type": "text/markdown",
            },
        )

    client = EmailTemplateApiClient(
        "http://testserver",
        transport=httpx.MockTransport(handler),
    )

    download = client.download_output("markdown")
    assert download.filename == "templates.md"
    assert download.content == b"# Email Templates\n"

