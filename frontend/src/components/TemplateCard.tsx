import { useState } from "react";
import { motion } from "motion/react";
import { Check, Copy, Hash, Layers3, Mail, Users } from "lucide-react";
import type { TemplateOut } from "../types/api";

interface TemplateCardProps {
  template: TemplateOut;
  index?: number;
}

export function TemplateCard({ template, index = 0 }: TemplateCardProps) {
  const [copied, setCopied] = useState(false);

  const meta = [
    { label: template.category, key: "category" },
    { label: template.tone, key: "tone" },
    { label: template.sentiment, key: "sentiment" },
    { label: template.intent, key: "intent" },
  ].filter((item): item is { label: string; key: string } => Boolean(item.label));

  function handleCopy() {
    if (!navigator.clipboard) return;
    void navigator.clipboard.writeText(template.body_template).then(() => {
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1400);
    });
  }

  return (
    <motion.article
      className="glass-card group relative overflow-hidden p-0"
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1], delay: Math.min(index * 0.04, 0.28) }}
      whileHover={{ y: -4 }}
    >
      <div
        className="pointer-events-none absolute -right-24 -top-24 h-48 w-48 rounded-full bg-cyan-400/10 blur-3xl transition-opacity duration-500 group-hover:bg-cyan-400/15"
        aria-hidden="true"
      />

      <div className="relative border-b border-white/[0.08] bg-white/[0.02] p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              {meta.length ? (
                meta.map((item) => (
                  <span key={item.key} className="badge">
                    {item.label}
                  </span>
                ))
              ) : (
                <span className="badge text-slate-400">uncategorized</span>
              )}
            </div>
            <div className="flex items-start gap-2">
              <Mail className="mt-1 h-4 w-4 shrink-0 text-cyan-300" aria-hidden="true" />
              <h3 className="text-lg font-semibold leading-snug text-white">
                {template.subject_template}
              </h3>
            </div>
          </div>

          <div className="rounded-2xl border border-white/[0.10] bg-white/[0.04] px-3.5 py-2.5 text-right">
            <div className="flex items-center justify-end gap-1.5 text-[11px] font-medium uppercase tracking-wider text-slate-500">
              <Layers3 className="h-3 w-3" aria-hidden="true" />
              Cluster {template.cluster_id}
            </div>
            <p className="mt-1 flex items-center justify-end gap-1.5 text-sm font-semibold text-white">
              <Users className="h-3.5 w-3.5 text-slate-400" aria-hidden="true" />
              {template.cluster_size.toLocaleString()} emails
            </p>
          </div>
        </div>
      </div>

      <div className="relative space-y-4 p-5">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.18em] text-slate-400">
            <Hash className="h-3.5 w-3.5 text-cyan-300" aria-hidden="true" />
            Template body
          </div>
          <button
            type="button"
            onClick={handleCopy}
            className="ghost-button"
            aria-label="Copy template body"
          >
            {copied ? (
              <>
                <Check className="h-3.5 w-3.5 text-emerald-300" aria-hidden="true" />
                Copied
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5" aria-hidden="true" />
                Copy
              </>
            )}
          </button>
        </div>

        <pre className="max-h-72 overflow-auto whitespace-pre-wrap rounded-2xl border border-white/[0.08] bg-black/30 p-4 font-sans text-sm leading-6 text-slate-200">
          {template.body_template}
        </pre>

        {template.placeholders?.length ? (
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-medium uppercase tracking-[0.2em] text-slate-500">
              Placeholders
            </span>
            {template.placeholders.slice(0, 6).map((placeholder) => (
              <span
                key={placeholder}
                className="rounded-full border border-cyan-300/20 bg-cyan-300/[0.08] px-2.5 py-1 font-mono text-[11px] font-medium text-cyan-100"
              >
                {`{${placeholder}}`}
              </span>
            ))}
            {template.placeholders.length > 6 ? (
              <span className="text-[11px] text-slate-500">
                +{template.placeholders.length - 6} more
              </span>
            ) : null}
          </div>
        ) : null}

        {typeof template.similarity_to_centroid === "number" ? (
          <p className="text-xs text-slate-500">
            Similarity to centroid:{" "}
            <span className="font-semibold text-slate-300">
              {(template.similarity_to_centroid * 100).toFixed(1)}%
            </span>
          </p>
        ) : null}
      </div>
    </motion.article>
  );
}
