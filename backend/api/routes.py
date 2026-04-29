"""HTTP routes for the email template generation backend."""

from __future__ import annotations

import time
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from backend import __version__
from backend.api.dependencies import (
    require_artifacts,
    settings_dep,
    state_dep,
)
from backend.config import Settings
from backend.core.data_loader import load_csv
from backend.core.fine_tuning import fine_tune_model
from backend.core.pipeline import (
    PipelineArtifacts,
    PipelineState,
    match_template,
    run_pipeline,
)
from backend.core.preprocessing import preprocess_dataframe
from backend.core.sentiment import SentimentAnalyzer
from backend.logging_config import get_logger
from backend.schemas import (
    EvaluationResponse,
    FineTuneRequest,
    FineTuneResponse,
    GenerateTemplateMatch,
    GenerateTemplateRequest,
    GenerateTemplateResponse,
    HealthResponse,
    PipelineRequest,
    PipelineResponse,
    TemplateOut,
    TemplatesResponse,
    UploadResponse,
)
from backend.utils.file_utils import ensure_dir, safe_filename

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health(
    settings: Settings = Depends(settings_dep),
    state: PipelineState = Depends(state_dep),
) -> HealthResponse:
    artifacts = state.get()
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=__version__,
        embedding_model=settings.embedding_model_name,
        fine_tuned_loaded=bool(artifacts and artifacts.fine_tuned_used),
        n_emails_loaded=len(artifacts.df) if artifacts else 0,
        n_templates=len(artifacts.templates) if artifacts else 0,
    )


@router.post(
    "/api/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["data"],
)
async def upload_csv(
    file: UploadFile = File(...),
    settings: Settings = Depends(settings_dep),
    state: PipelineState = Depends(state_dep),
) -> UploadResponse:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .csv files are accepted.",
        )

    raw_dir = ensure_dir(settings.raw_data_dir)
    target = raw_dir / safe_filename(file.filename)
    contents = await file.read()
    target.write_bytes(contents)

    try:
        df = load_csv(target)
    except Exception as exc:
        target.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse CSV: {exc}",
        ) from exc

    state.last_uploaded_csv = target
    return UploadResponse(
        filename=file.filename,
        rows=len(df),
        columns=list(df.columns),
        saved_path=str(target),
        message="CSV uploaded and validated successfully.",
    )


@router.post("/api/run-pipeline", response_model=PipelineResponse, tags=["pipeline"])
def run_pipeline_endpoint(
    payload: PipelineRequest,
    settings: Settings = Depends(settings_dep),
) -> PipelineResponse:
    try:
        artifacts = run_pipeline(
            csv_path=payload.csv_path,
            use_fine_tuned=payload.use_fine_tuned,
            n_clusters=payload.n_clusters,
            clustering_method=payload.clustering_method,
            settings=settings,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return PipelineResponse(
        status="completed",
        n_emails=len(artifacts.df),
        n_clusters=artifacts.clustering.n_clusters,
        n_templates=len(artifacts.templates),
        evaluation=artifacts.evaluation,
        templates_csv=str(artifacts.output_paths["csv"]),
        templates_json=str(artifacts.output_paths["json"]),
        templates_md=str(artifacts.output_paths["md"]),
        duration_seconds=artifacts.duration_seconds,
    )


@router.post("/api/fine-tune", response_model=FineTuneResponse, tags=["pipeline"])
def fine_tune_endpoint(
    payload: FineTuneRequest,
    settings: Settings = Depends(settings_dep),
) -> FineTuneResponse:
    start = time.perf_counter()
    try:
        df = (
            load_csv(payload.csv_path)
            if payload.csv_path
            else (
                load_csv(settings.sample_csv)
                if settings.sample_csv.exists()
                else None
            )
        )
        if df is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No dataset found. Upload one first or provide csv_path.",
            )
        df = preprocess_dataframe(df)
        outcome = fine_tune_model(
            df,
            text_column="combined_text",
            epochs=payload.epochs,
            batch_size=payload.batch_size,
            use_pseudo_labels=payload.use_pseudo_labels,
            settings=settings,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - integration failure mode
        logger.exception("Fine-tune failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc

    return FineTuneResponse(
        status="completed",
        model_path=outcome.model_path,
        epochs=outcome.epochs,
        n_pairs=outcome.n_pairs,
        baseline_silhouette=outcome.baseline_silhouette,
        fine_tuned_silhouette=outcome.fine_tuned_silhouette,
        improvement=outcome.improvement,
        duration_seconds=outcome.duration_seconds,
    )


def _to_template_out(artifacts) -> List[TemplateOut]:
    return [TemplateOut(**t.to_dict()) for t in artifacts.templates]


@router.get("/api/templates", response_model=TemplatesResponse, tags=["templates"])
def list_templates(
    artifacts: PipelineArtifacts = Depends(require_artifacts),
) -> TemplatesResponse:
    items = _to_template_out(artifacts)
    return TemplatesResponse(count=len(items), templates=items)


@router.get(
    "/api/templates/{template_id}",
    response_model=TemplateOut,
    tags=["templates"],
)
def get_template(
    template_id: str,
    artifacts: PipelineArtifacts = Depends(require_artifacts),
) -> TemplateOut:
    for tpl in artifacts.templates:
        if tpl.template_id == template_id:
            return TemplateOut(**tpl.to_dict())
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail=f"Template {template_id} not found"
    )


@router.get("/api/evaluation", response_model=EvaluationResponse, tags=["pipeline"])
def get_evaluation(
    artifacts: PipelineArtifacts = Depends(require_artifacts),
) -> EvaluationResponse:
    metrics = artifacts.evaluation
    return EvaluationResponse(**metrics)


@router.get("/api/outputs/{file_format}", tags=["templates"])
def download_output(
    file_format: str,
    artifacts: PipelineArtifacts = Depends(require_artifacts),
) -> FileResponse:
    """Download the latest generated templates in CSV, JSON, or Markdown format."""

    normalized = file_format.lower()
    key = "md" if normalized in {"md", "markdown"} else normalized
    if key not in {"csv", "json", "md"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="file_format must be one of: csv, json, markdown.",
        )

    path = artifacts.output_paths.get(key)
    if path is None or not Path(path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generated {file_format} output was not found. Run the pipeline again.",
        )

    media_types = {
        "csv": "text/csv",
        "json": "application/json",
        "md": "text/markdown",
    }
    extensions = {"csv": "csv", "json": "json", "md": "md"}
    return FileResponse(
        path=path,
        media_type=media_types[key],
        filename=f"templates.{extensions[key]}",
    )


@router.post(
    "/api/generate-template",
    response_model=GenerateTemplateResponse,
    tags=["templates"],
)
def generate_template_endpoint(
    payload: GenerateTemplateRequest,
    settings: Settings = Depends(settings_dep),
    artifacts: PipelineArtifacts = Depends(require_artifacts),
) -> GenerateTemplateResponse:
    try:
        matches = match_template(payload.body, subject=payload.subject, top_k=payload.top_k)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    analyzer = SentimentAnalyzer(settings=settings)
    sentiment = analyzer.analyze(f"{payload.subject or ''}\n\n{payload.body}")

    return GenerateTemplateResponse(
        matches=[
            GenerateTemplateMatch(
                template=TemplateOut(**m["template"].to_dict()),
                similarity=m["similarity"],
            )
            for m in matches
        ],
        detected_tone=sentiment.tone,
        detected_sentiment=sentiment.sentiment,
    )
