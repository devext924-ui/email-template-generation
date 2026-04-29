export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  embedding_model: string;
  fine_tuned_loaded: boolean;
  n_emails_loaded: number;
  n_templates: number;
}

export interface UploadResponse {
  filename: string;
  rows: number;
  columns: string[];
  saved_path: string;
  message: string;
}

export interface PipelineRequest {
  csv_path?: string | null;
  use_fine_tuned?: boolean | null;
  n_clusters?: number | null;
  clustering_method?: "kmeans" | "dbscan" | "agglomerative" | null;
}

export interface PipelineResponse {
  status: string;
  n_emails: number;
  n_clusters: number;
  n_templates: number;
  evaluation: EvaluationResponse;
  templates_csv: string;
  templates_json: string;
  templates_md: string;
  duration_seconds: number;
}

export interface FineTuneRequest {
  csv_path?: string | null;
  epochs?: number | null;
  batch_size?: number | null;
  use_pseudo_labels: boolean;
}

export interface FineTuneResponse {
  status: string;
  model_path: string;
  epochs: number;
  n_pairs: number;
  baseline_silhouette?: number | null;
  fine_tuned_silhouette?: number | null;
  improvement?: number | null;
  duration_seconds: number;
}

export interface TemplateOut {
  template_id: string;
  cluster_id: number;
  cluster_size: number;
  category?: string | null;
  tone?: string | null;
  sentiment?: string | null;
  intent?: string | null;
  subject_template: string;
  body_template: string;
  placeholders: string[];
  representative_email_id?: string | null;
  similarity_to_centroid?: number | null;
}

export interface TemplatesResponse {
  count: number;
  templates: TemplateOut[];
}

export interface EvaluationResponse {
  n_emails: number;
  n_clusters: number;
  n_templates: number;
  silhouette_score?: number | null;
  davies_bouldin_score?: number | null;
  average_intra_cluster_similarity?: number | null;
  cluster_sizes: Record<string, number>;
  template_coverage: number;
  duplicate_template_percentage: number;
  average_template_length: number;
  average_readability?: number | null;
  baseline_silhouette?: number | null;
  fine_tuned_silhouette?: number | null;
  fine_tuning_improvement?: number | null;
  generated_at?: string;
}

export interface GenerateTemplateRequest {
  subject?: string | null;
  body: string;
  top_k: number;
}

export interface GenerateTemplateMatch {
  template: TemplateOut;
  similarity: number;
}

export interface GenerateTemplateResponse {
  matches: GenerateTemplateMatch[];
  detected_tone?: string | null;
  detected_sentiment?: string | null;
}

export interface ApiErrorPayload {
  detail?: string | Array<{ msg?: string; [key: string]: unknown }>;
}
