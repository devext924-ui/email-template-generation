"""CLI behavior tests."""

from __future__ import annotations

from pathlib import Path

import cli
from frontend.api_client import ApiClientError


class FakeClient:
    def __init__(self) -> None:
        self.uploaded: list[str] = []

    def upload_csv(self, filename: str, content: bytes, *, content_type: str = "text/csv"):
        self.uploaded.append(filename)
        assert content_type == "text/csv"
        assert b"email_id,subject,body" in content
        return {
            "filename": filename,
            "rows": 1,
            "columns": ["email_id", "subject", "body"],
            "saved_path": "/tmp/backend/raw/emails.csv",
            "message": "ok",
        }

    def run_pipeline(self, **kwargs):
        assert kwargs["csv_path"] == "/tmp/backend/raw/emails.csv"
        return {
            "status": "completed",
            "n_emails": 1,
            "n_clusters": 1,
            "n_templates": 1,
            "evaluation": {"silhouette_score": 0.42},
            "templates_csv": "outputs/templates.csv",
            "templates_json": "outputs/templates.json",
            "templates_md": "outputs/templates.md",
            "duration_seconds": 0.1,
        }

    def get_evaluation(self):
        return {
            "n_emails": 1,
            "n_clusters": 1,
            "n_templates": 1,
            "silhouette_score": 0.42,
            "cluster_sizes": {"0": 1},
        }


class EmptyStateClient(FakeClient):
    def get_evaluation(self):
        raise ApiClientError("Pipeline has not been run yet.", status_code=409)


def test_cli_run_uploads_input_and_prints_summary(monkeypatch, tmp_path, capsys):
    csv_path = tmp_path / "emails.csv"
    csv_path.write_text("email_id,subject,body\n1,Hello,Body\n", encoding="utf-8")
    fake = FakeClient()
    monkeypatch.setattr(cli, "build_client", lambda _args: fake)

    code = cli.main(["run", "--input", str(csv_path), "--clusters", "1"])

    assert code == 0
    assert fake.uploaded == ["emails.csv"]
    output = capsys.readouterr().out
    assert "Pipeline completed" in output
    assert "Templates: 1" in output


def test_cli_metrics_can_print_backend_metrics(monkeypatch, capsys):
    monkeypatch.setattr(cli, "build_client", lambda _args: FakeClient())

    code = cli.main(["metrics"])

    assert code == 0
    output = capsys.readouterr().out
    assert "Evaluation metrics" in output
    assert "silhouette_score: 0.42" in output


def test_cli_metrics_falls_back_to_sample_for_local_empty_state(monkeypatch, tmp_path, capsys):
    sample = tmp_path / "sample_emails.csv"
    sample.write_text("email_id,subject,body\n1,Hello,Body\n", encoding="utf-8")
    monkeypatch.setattr(cli, "SAMPLE_CSV", sample)
    monkeypatch.setattr(cli, "build_client", lambda _args: EmptyStateClient())
    monkeypatch.delenv("EMAIL_TEMPLATE_BACKEND_URL", raising=False)
    monkeypatch.delenv("BACKEND_URL", raising=False)

    code = cli.main(["metrics"])

    assert code == 0
    output = capsys.readouterr().out
    assert "running the bundled sample dataset" in output
    assert "Evaluation metrics" in output


def test_cli_templates_reads_generated_markdown(monkeypatch, tmp_path, capsys):
    markdown = tmp_path / "templates.md"
    markdown.write_text("# Email Templates\n\n## tmpl_123\n", encoding="utf-8")
    monkeypatch.setattr(cli, "OUTPUT_FILES", {"markdown": markdown, "csv": Path(), "json": Path()})
    monkeypatch.delenv("EMAIL_TEMPLATE_BACKEND_URL", raising=False)
    monkeypatch.delenv("BACKEND_URL", raising=False)

    code = cli.main(["templates", "--format", "markdown"])

    assert code == 0
    assert "# Email Templates" in capsys.readouterr().out
