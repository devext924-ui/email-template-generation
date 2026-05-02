import { motion } from "motion/react";
import {
  BarChart3,
  Boxes,
  CircleDot,
  FileText,
  Gauge,
  Repeat2,
  Sparkles,
  TrendingUp,
} from "lucide-react";
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
          <p>
            Cluster quality, template coverage, and duplication scores will appear here once a pipeline run
            completes.
          </p>
        </div>
        <EmptyState
          icon={<Sparkles className="h-6 w-6" aria-hidden="true" />}
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
      helper: "Higher means cleaner cluster separation",
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
      label: "Duplicate templates",
      value: formatPercent(evaluation.duplicate_template_percentage),
      helper: `${formatNumber(evaluation.average_template_length, 0)} avg body chars`,
    },
  ];

  const fineTuneImprovement = evaluation.fine_tuning_improvement;
  const showFineTuneCallout =
    fineTuneImprovement !== null &&
    fineTuneImprovement !== undefined &&
    !Number.isNaN(fineTuneImprovement);

  return (
    <section className="section-shell" id="metrics">
      <div className="section-heading">
        <p className="section-kicker">Evaluation</p>
        <h2>Metrics dashboard</h2>
        <p>
          {pipelineResult ? (
            <>
              Latest run completed in{" "}
              <span className="font-semibold text-white">
                {pipelineResult.duration_seconds.toFixed(2)}s
              </span>
              .
            </>
          ) : (
            <>Cluster quality, coverage, and duplication metrics from the most recent pipeline run.</>
          )}
        </p>
      </div>

      {showFineTuneCallout ? (
        <motion.div
          className="glass-card mb-6 flex flex-wrap items-center gap-4 p-5"
          initial={{ opacity: 0, y: 14 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 0.4 }}
        >
          <div className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-violet-500 to-fuchsia-400 text-white shadow-glow-violet">
            <TrendingUp className="h-5 w-5" aria-hidden="true" />
          </div>
          <div className="flex-1">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-violet-200">
              Fine-tuning impact
            </p>
            <p className="mt-1 text-sm leading-6 text-slate-300">
              Silhouette score moved from{" "}
              <span className="font-semibold text-white">
                {formatNumber(evaluation.baseline_silhouette, 3)}
              </span>{" "}
              to{" "}
              <span className="font-semibold text-white">
                {formatNumber(evaluation.fine_tuned_silhouette, 3)}
              </span>{" "}
              ({fineTuneImprovement! >= 0 ? "+" : ""}
              {fineTuneImprovement!.toFixed(3)}).
            </p>
          </div>
        </motion.div>
      ) : null}

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
