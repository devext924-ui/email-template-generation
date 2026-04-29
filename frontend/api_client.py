"""HTTP client used by the Streamlit frontend and integration tests."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, BinaryIO

import httpx


DEFAULT_BACKEND_URL = "http://127.0.0.1:8000"


def configured_backend_url() -> str:
    """Return the backend URL from environment, falling back to local FastAPI."""

    return (
        os.getenv("EMAIL_TEMPLATE_BACKEND_URL")
        or os.getenv("BACKEND_URL")
        or DEFAULT_BACKEND_URL
    ).rstrip("/")


class ApiClientError(RuntimeError):
    """Raised when the backend returns an error response."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class BackendUnavailableError(ApiClientError):
    """Raised when the configured backend cannot be reached."""


@dataclass(frozen=True)
class DownloadedFile:
    """A generated output file returned by the backend."""

    content: bytes
    filename: str
    content_type: str


class EmailTemplateApiClient:
    """Small, typed wrapper around the FastAPI contract."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        timeout: float = 120.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = (base_url or configured_backend_url()).rstrip("/")
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            transport=transport,
            follow_redirects=True,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "EmailTemplateApiClient":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def upload_csv(
        self,
        filename: str,
        content: bytes | BinaryIO,
        *,
        content_type: str = "text/csv",
    ) -> dict[str, Any]:
        files = {"file": (filename, content, content_type)}
        return self._request("POST", "/api/upload", files=files)

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
        return self._request("POST", "/api/run-pipeline", json=payload)

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
        return self._request("POST", "/api/fine-tune", json=payload)

    def list_templates(self) -> dict[str, Any]:
        return self._request("GET", "/api/templates")

    def get_template(self, template_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/templates/{template_id}")

    def get_evaluation(self) -> dict[str, Any]:
        return self._request("GET", "/api/evaluation")

    def generate_template(
        self,
        *,
        body: str,
        subject: str | None = None,
        top_k: int = 1,
    ) -> dict[str, Any]:
        payload = {"subject": subject, "body": body, "top_k": top_k}
        return self._request("POST", "/api/generate-template", json=payload)

    def download_output(self, file_format: str) -> DownloadedFile:
        response = self._raw_request("GET", f"/api/outputs/{file_format}")
        filename = _filename_from_headers(response.headers) or f"templates.{_extension(file_format)}"
        return DownloadedFile(
            content=response.content,
            filename=filename,
            content_type=response.headers.get("content-type", "application/octet-stream"),
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        response = self._raw_request(method, path, **kwargs)
        if not response.content:
            return {}
        return response.json()

    def _raw_request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.TimeoutException as exc:
            raise BackendUnavailableError(
                f"The backend at {self.base_url} timed out. Is the FastAPI server still running?"
            ) from exc
        except httpx.RequestError as exc:
            raise BackendUnavailableError(
                f"Could not reach the backend at {self.base_url}. Start it with: "
                "uvicorn backend.main:app --reload"
            ) from exc

        if response.status_code >= 400:
            raise ApiClientError(
                _error_detail(response),
                status_code=response.status_code,
            )
        return response


def _drop_none(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def _error_detail(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        text = response.text.strip()
        return text or f"Backend returned HTTP {response.status_code}."

    detail = body.get("detail", body)
    if isinstance(detail, list):
        return "; ".join(str(item.get("msg", item)) for item in detail)
    return str(detail)


def _filename_from_headers(headers: httpx.Headers) -> str | None:
    disposition = headers.get("content-disposition")
    if not disposition:
        return None
    for part in disposition.split(";"):
        part = part.strip()
        if part.startswith("filename="):
            return part.removeprefix("filename=").strip('"')
    return None


def _extension(file_format: str) -> str:
    return "md" if file_format.lower() in {"markdown", "md"} else file_format.lower()

