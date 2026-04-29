"""Pydantic schemas used by the FastAPI layer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Service status indicator")
    app_name: str
    version: str
    embedding_model: str
    fine_tuned_loaded: bool = False
    n_emails_loaded: int = 0
    n_templates: int = 0


class UploadResponse(BaseModel):
    filename: str
    rows: int
    columns: List[str]
    saved_path: str
    message: str


class PipelineRequest(BaseModel):
    csv_path: Optional[str] = Field(
        default=None,
        description="Optional explicit path to a dataset. Defaults to most recently uploaded file or sample data.",
    )
    use_fine_tuned: Optional[bool] = Field(
        default=None,
        description="Override config to load the fine-tuned model when running embeddings.",
    )
    n_clusters: Optional[int] = Field(
        default=None,
        description="Override the number of clusters; if omitted, uses heuristic.",
    )
    clustering_method: Optional[str] = Field(default=None)


class PipelineResponse(BaseModel):
    status: str
    n_emails: int
    n_clusters: int
    n_templates: int
    evaluation: Dict[str, Any]
    templates_csv: str
    templates_json: str
    templates_md: str
    duration_seconds: float


class FineTuneRequest(BaseModel):
    csv_path: Optional[str] = None
    epochs: Optional[int] = None
    batch_size: Optional[int] = None
    use_pseudo_labels: bool = True


class FineTuneResponse(BaseModel):
    status: str
    model_path: str
    epochs: int
    n_pairs: int
    baseline_silhouette: Optional[float]
    fine_tuned_silhouette: Optional[float]
    improvement: Optional[float]
    duration_seconds: float


class TemplateOut(BaseModel):
    template_id: str
    cluster_id: int
    cluster_size: int
    category: Optional[str] = None
    tone: Optional[str] = None
    sentiment: Optional[str] = None
    intent: Optional[str] = None
    subject_template: str
    body_template: str
    placeholders: List[str] = Field(default_factory=list)
    representative_email_id: Optional[str] = None
    similarity_to_centroid: Optional[float] = None


class TemplatesResponse(BaseModel):
    count: int
    templates: List[TemplateOut]


class EvaluationResponse(BaseModel):
    n_emails: int
    n_clusters: int
    n_templates: int
    silhouette_score: Optional[float]
    davies_bouldin_score: Optional[float]
    average_intra_cluster_similarity: Optional[float]
    cluster_sizes: Dict[str, int]
    template_coverage: float
    duplicate_template_percentage: float
    average_template_length: float
    average_readability: Optional[float]
    baseline_silhouette: Optional[float] = None
    fine_tuned_silhouette: Optional[float] = None
    fine_tuning_improvement: Optional[float] = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GenerateTemplateRequest(BaseModel):
    subject: Optional[str] = None
    body: str = Field(..., min_length=1)
    top_k: int = Field(default=1, ge=1, le=5)


class GenerateTemplateMatch(BaseModel):
    template: TemplateOut
    similarity: float


class GenerateTemplateResponse(BaseModel):
    matches: List[GenerateTemplateMatch]
    detected_tone: Optional[str] = None
    detected_sentiment: Optional[str] = None


class ErrorResponse(BaseModel):
    detail: str
