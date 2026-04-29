import { BarChart3, Boxes, CircleDot, FileText, Gauge, Repeat2 } from "lucide-react";
import type { EvaluationResponse, PipelineResponse } from "../types/api";
import { MetricCard } from "./MetricCard";
import { EmptyState } from "./EmptyState";

interface EvaluationPanelProps {
  evaluation: EvaluationResponse | null;
  pipelineResult: PipelineResponse | null;
}

export function EvaluationPanel({ evaluation, pipelineResult }: EvaluationPanelProps) {
  if (!evaluation) {
    return (
      <section className="section-shell" id="metrics">
        <div className="section-heading">
          <p className="section-kicker">Evaluation</p>
          <h2>Metrics dashboard</h2>
        </div>
        <EmptyState
          title="Metrics will appear after a pipeline run"
          description="Run the backend pipeline to calculate cluster quality, template coverage, duplication, and template length metrics."
        />
      </section>
    );
  }

  const metrics = [
    {
      icon: FileText,
      label: "Templates generated",
      value: evaluation.n_templates,
      helper: `${evaluation.n_emails.toLocaleString()} emails processed`,
    },
    {
      icon: Boxes,
      label: "Clusters discovered",
      value: evaluation.n_clusters,
      helper: "Semantic groups from embeddings",
    },
    {
      icon: Gauge,
      label: "Silhouette score",
      value: formatNumber(evaluation.silhouette_score, 3),
      helper: "Higher means cleaner separation",
    },
    {
      icon: CircleDot,
      label: "Cluster similarity",
      value: formatNumber(evaluation.average_intra_cluster_similarity, 3),
      helper: "Average in-cluster cosine similarity",
    },
    {
      icon: BarChart3,
      label: "Template coverage",
      value: formatPercent(evaluation.template_coverage),
      helper: "Emails represented by generated templates",
    },
    {
      icon: Repeat2,
      label: "Duplicate percentage",
      value: formatPercent(evaluation.duplicate_template_percentage),
      helper: `${formatNumber(evaluation.average_template_length, 0)} avg body chars`,
    },
  ];

  return (
    <section className="section-shell" id="metrics">
      <div className="section-heading">
        <p className="section-kicker">Evaluation</p>
        <h2>Metrics dashboard</h2>
        <p>
          Latest run completed in{" "}
          <span className="text-slate-100">
            {pipelineResult ? `${pipelineResult.duration_seconds.toFixed(2)}s` : "n/a"}
          </span>
          .
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {metrics.map((metric) => (
          <MetricCard key={metric.label} {...metric} />
        ))}
      </div>
    </section>
  );
}

function formatNumber(value?: number | null, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) return "n/a";
  return value.toFixed(digits);
}

function formatPercent(value?: number | null) {
  if (value === null || value === undefined || Number.isNaN(value)) return "n/a";
  return `${(value * 100).toFixed(1)}%`;
}
