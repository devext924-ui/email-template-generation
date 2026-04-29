"""Command-line interface for the email template generation project."""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from frontend.api_client import (
    ApiClientError,
    DownloadedFile,
    EmailTemplateApiClient,
)


PROJECT_ROOT = Path(__file__).resolve().parent
SAMPLE_CSV = PROJECT_ROOT / "data" / "sample_emails.csv"
OUTPUT_FILES = {
    "csv": PROJECT_ROOT / "outputs" / "templates.csv",
    "json": PROJECT_ROOT / "outputs" / "templates.json",
    "markdown": PROJECT_ROOT / "outputs" / "templates.md",
}


class LocalApiClient:
    """Exercise the FastAPI app in-process when no server URL is provided."""

    def __init__(self) -> None:
        from fastapi.testclient import TestClient

        from backend.main import create_app

        self._client = TestClient(create_app())

    def health(self) -> dict[str, Any]:
        return self._json(self._client.get("/health"))

    def upload_csv(self, filename: str, content: bytes, *, content_type: str = "text/csv") -> dict[str, Any]:
        response = self._client.post(
            "/api/upload",
            files={"file": (filename, content, content_type)},
        )
        return self._json(response)

    def run_pipeline(
        self,
        *,
        csv_path: str | None = None,
        use_fine_tuned: bool | None = None,
        n_clusters: int | None = None,
        clustering_method: str | None = None,
    ) -> dict[str, Any]:
        payload = _drop_none(
            {
                "csv_path": csv_path,
                "use_fine_tuned": use_fine_tuned,
                "n_clusters": n_clusters,
                "clustering_method": clustering_method,
            }
        )
        return self._json(self._client.post("/api/run-pipeline", json=payload))

    def fine_tune(
        self,
        *,
        csv_path: str | None = None,
        epochs: int | None = None,
        batch_size: int | None = None,
        use_pseudo_labels: bool = True,
    ) -> dict[str, Any]:
        payload = _drop_none(
            {
                "csv_path": csv_path,
                "epochs": epochs,
                "batch_size": batch_size,
                "use_pseudo_labels": use_pseudo_labels,
            }
        )
        return self._json(self._client.post("/api/fine-tune", json=payload))

    def list_templates(self) -> dict[str, Any]:
        return self._json(self._client.get("/api/templates"))

    def get_evaluation(self) -> dict[str, Any]:
        return self._json(self._client.get("/api/evaluation"))

    def download_output(self, file_format: str) -> DownloadedFile:
        response = self._client.get(f"/api/outputs/{file_format}")
        if response.status_code >= 400:
            raise ApiClientError(_response_detail(response), status_code=response.status_code)
        filename = _filename_from_content_disposition(response.headers.get("content-disposition"))
        return DownloadedFile(
            content=response.content,
            filename=filename or f"templates.{_extension(file_format)}",
            content_type=response.headers.get("content-type", "application/octet-stream"),
        )

    @staticmethod
    def _json(response: Any) -> dict[str, Any]:
        if response.status_code >= 400:
            raise ApiClientError(_response_detail(response), status_code=response.status_code)
        return response.json()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Email Template Generation backend from the command line.",
    )
    parser.add_argument(
        "--backend-url",
        default=None,
        help=(
            "Optional running FastAPI URL. If omitted, the CLI uses the FastAPI app "
            "in-process so commands work without a separate server."
        ),
    )
    parser.add_argument("--timeout", type=float, default=300.0, help="HTTP timeout in seconds.")
    parser.add_argument("--verbose", action="store_true", help="Show backend and HTTP logs.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    sample = subparsers.add_parser(
        "load-sample",
        aliases=["sample"],
        help="Copy the bundled sample dataset into data/raw.",
    )
    sample.add_argument(
        "--destination",
        default="data/raw/emails.csv",
        help="Destination path for the sample CSV.",
    )
    sample.add_argument(
        "--upload",
        action="store_true",
        help="Also upload the copied sample CSV to the configured backend.",
    )
    sample.set_defaults(func=cmd_load_sample)

    run = subparsers.add_parser("run", help="Upload a CSV and run the full pipeline.")
    run.add_argument("--input", "-i", default=None, help="Input CSV path.")
    run.add_argument(
        "--method",
        choices=["kmeans", "dbscan", "agglomerative"],
        default="kmeans",
        help="Clustering method.",
    )
    run.add_argument("--clusters", type=int, default=None, help="Optional cluster count.")
    run.add_argument(
        "--use-fine-tuned",
        action="store_true",
        help="Use the saved fine-tuned Sentence Transformer if available.",
    )
    run.add_argument("--json", action="store_true", dest="json_output", help="Print raw JSON.")
    run.set_defaults(func=cmd_run)

    fine_tune = subparsers.add_parser("fine-tune", help="Fine-tune the embedding model.")
    fine_tune.add_argument("--input", "-i", default=None, help="Input CSV path.")
    fine_tune.add_argument("--epochs", type=int, default=1, help="Fine-tuning epochs.")
    fine_tune.add_argument("--batch-size", type=int, default=16, help="Fine-tuning batch size.")
    fine_tune.add_argument(
        "--no-pseudo-labels",
        action="store_true",
        help="Disable pseudo-label generation for weakly supervised pairs.",
    )
    fine_tune.add_argument("--json", action="store_true", dest="json_output", help="Print raw JSON.")
    fine_tune.set_defaults(func=cmd_fine_tune)

    templates = subparsers.add_parser("templates", help="Export generated templates.")
    templates.add_argument(
        "--format",
        choices=["csv", "json", "markdown"],
        default="markdown",
        help="Export format.",
    )
    templates.add_argument("--output", "-o", default=None, help="Optional output file path.")
    templates.set_defaults(func=cmd_templates)

    metrics = subparsers.add_parser("metrics", help="View latest evaluation metrics.")
    metrics.add_argument(
        "--input",
        "-i",
        default=None,
        help="Optional CSV to run first when no backend server state exists.",
    )
    metrics.add_argument("--json", action="store_true", dest="json_output", help="Print raw JSON.")
    metrics.set_defaults(func=cmd_metrics)

    health = subparsers.add_parser("health", help="Check backend health.")
    health.set_defaults(func=cmd_health)

    return parser


def build_client(args: argparse.Namespace) -> EmailTemplateApiClient | LocalApiClient:
    backend_url = args.backend_url or os.getenv("EMAIL_TEMPLATE_BACKEND_URL") or os.getenv("BACKEND_URL")
    if backend_url:
        client: EmailTemplateApiClient | LocalApiClient = EmailTemplateApiClient(
            backend_url, timeout=args.timeout
        )
    else:
        client = LocalApiClient()
    _configure_cli_logging(verbose=args.verbose)
    return client


def cmd_health(args: argparse.Namespace) -> int:
    client = build_client(args)
    print(json.dumps(client.health(), indent=2))
    return 0


def cmd_load_sample(args: argparse.Namespace) -> int:
    _ensure_sample_exists()
    destination = _project_path(args.destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.resolve() != SAMPLE_CSV.resolve():
        shutil.copyfile(SAMPLE_CSV, destination)
    print(f"Sample data ready: {_display_path(destination)}")

    if args.upload:
        client = build_client(args)
        result = client.upload_csv(destination.name, destination.read_bytes())
        print(f"Uploaded to backend path: {result['saved_path']}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    client = build_client(args)
    csv_path = _upload_input(client, args.input) if args.input else None
    result = client.run_pipeline(
        csv_path=csv_path,
        use_fine_tuned=args.use_fine_tuned,
        n_clusters=args.clusters,
        clustering_method=args.method,
    )
    if args.json_output:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_pipeline_result(result)
    return 0


def cmd_fine_tune(args: argparse.Namespace) -> int:
    client = build_client(args)
    csv_path = _upload_input(client, args.input) if args.input else None
    result = client.fine_tune(
        csv_path=csv_path,
        epochs=args.epochs,
        batch_size=args.batch_size,
        use_pseudo_labels=not args.no_pseudo_labels,
    )
    if args.json_output:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("Fine-tuning completed")
        print(f"Model path: {result['model_path']}")
        print(f"Training pairs: {result['n_pairs']}")
        print(f"Improvement: {_format_optional_float(result.get('improvement'))}")
        print(f"Duration: {result['duration_seconds']:.2f}s")
    return 0


def cmd_templates(args: argparse.Namespace) -> int:
    if _uses_http_backend(args):
        client = build_client(args)
        download = client.download_output(args.format)
        content = download.content
        default_name = download.filename
    else:
        output_path = OUTPUT_FILES[args.format]
        if not output_path.exists():
            raise ApiClientError(
                f"{output_path.relative_to(PROJECT_ROOT)} does not exist. Run the pipeline first."
            )
        content = output_path.read_bytes()
        default_name = output_path.name

    if args.output:
        destination = _project_path(args.output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        print(f"Wrote {destination}")
    else:
        text = content.decode("utf-8")
        print(text if args.format != "json" else json.dumps(json.loads(text), indent=2))
    if args.output:
        print(f"Format: {args.format} ({default_name})")
    return 0


def cmd_metrics(args: argparse.Namespace) -> int:
    client = build_client(args)
    if args.input:
        csv_path = _upload_input(client, args.input)
        result = client.run_pipeline(csv_path=csv_path)
        metrics = result["evaluation"]
    else:
        try:
            metrics = client.get_evaluation()
        except ApiClientError as exc:
            if _uses_http_backend(args) or exc.status_code != 409:
                raise
            print("No active local pipeline state found; running the bundled sample dataset.")
            _ensure_sample_exists()
            csv_path = _upload_input(client, str(SAMPLE_CSV))
            result = client.run_pipeline(csv_path=csv_path)
            metrics = result["evaluation"]

    if args.json_output:
        print(json.dumps(metrics, indent=2, default=str))
    else:
        _print_metrics(metrics)
    return 0


def _upload_input(client: EmailTemplateApiClient | LocalApiClient, raw_path: str) -> str:
    input_path = _project_path(raw_path)
    if not input_path.exists():
        raise ApiClientError(f"Input CSV not found: {input_path}")
    result = client.upload_csv(input_path.name, input_path.read_bytes())
    print(f"Uploaded {_display_path(input_path)} ({result['rows']} rows)")
    return result["saved_path"]


def _print_pipeline_result(result: dict[str, Any]) -> None:
    print("Pipeline completed")
    print(f"Emails: {result['n_emails']}")
    print(f"Clusters: {result['n_clusters']}")
    print(f"Templates: {result['n_templates']}")
    print(f"Duration: {result['duration_seconds']:.2f}s")
    print("Outputs:")
    print(f"  CSV: {result['templates_csv']}")
    print(f"  JSON: {result['templates_json']}")
    print(f"  Markdown: {result['templates_md']}")
    evaluation = result.get("evaluation", {})
    print(f"Silhouette: {_format_optional_float(evaluation.get('silhouette_score'))}")


def _print_metrics(metrics: dict[str, Any]) -> None:
    print("Evaluation metrics")
    for key in (
        "n_emails",
        "n_clusters",
        "n_templates",
        "silhouette_score",
        "davies_bouldin_score",
        "average_intra_cluster_similarity",
        "template_coverage",
        "duplicate_template_percentage",
        "average_template_length",
        "average_readability",
    ):
        print(f"{key}: {metrics.get(key)}")
    cluster_sizes = metrics.get("cluster_sizes") or {}
    if cluster_sizes:
        print(f"cluster_sizes: {len(cluster_sizes)} clusters")


def _ensure_sample_exists() -> None:
    if SAMPLE_CSV.exists():
        return
    from backend.core.data_loader import generate_sample_dataset

    SAMPLE_CSV.parent.mkdir(parents=True, exist_ok=True)
    generate_sample_dataset().to_csv(SAMPLE_CSV, index=False)


def _project_path(path: str) -> Path:
    candidate = Path(path).expanduser()
    return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _uses_http_backend(args: argparse.Namespace) -> bool:
    return bool(args.backend_url or os.getenv("EMAIL_TEMPLATE_BACKEND_URL") or os.getenv("BACKEND_URL"))


def _configure_cli_logging(*, verbose: bool) -> None:
    level = logging.INFO if verbose else logging.WARNING
    for name in ("backend", "httpx", "sentence_transformers", "transformers"):
        logging.getLogger(name).setLevel(level)
    if logging.getLogger().handlers and not verbose:
        logging.getLogger().setLevel(logging.WARNING)


def _format_optional_float(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):.4f}"


def _drop_none(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def _response_detail(response: Any) -> str:
    try:
        body = response.json()
    except ValueError:
        return response.text
    return str(body.get("detail", body))


def _filename_from_content_disposition(disposition: str | None) -> str | None:
    if not disposition:
        return None
    for part in disposition.split(";"):
        part = part.strip()
        if part.startswith("filename="):
            return part.removeprefix("filename=").strip('"')
    return None


def _extension(file_format: str) -> str:
    return "md" if file_format == "markdown" else file_format


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ApiClientError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
