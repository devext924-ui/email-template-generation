import { motion } from "motion/react";
import { Copy, Layers3, MessageSquareText } from "lucide-react";
import type { TemplateOut } from "../types/api";

interface TemplateCardProps {
  template: TemplateOut;
  index?: number;
}

export function TemplateCard({ template, index = 0 }: TemplateCardProps) {
  const meta = [
    template.category,
    template.tone,
    template.sentiment,
    template.intent,
  ].filter(Boolean);

  return (
    <motion.article
      className="glass-card overflow-hidden p-0"
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.42, delay: Math.min(index * 0.035, 0.24) }}
      whileHover={{ y: -4, scale: 1.005 }}
    >
      <div className="border-b border-white/10 bg-white/[0.035] p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="mb-3 flex flex-wrap gap-2">
              {meta.length ? (
                meta.map((item) => (
                  <span
                    key={item}
                    className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-slate-300"
                  >
                    {item}
                  </span>
                ))
              ) : (
                <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-slate-300">
                  uncategorized
                </span>
              )}
            </div>
            <h3 className="text-lg font-semibold leading-snug text-white">
              {template.subject_template}
            </h3>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-right">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <Layers3 className="h-3.5 w-3.5" aria-hidden="true" />
              Cluster {template.cluster_id}
            </div>
            <p className="mt-1 text-sm font-semibold text-white">
              {template.cluster_size} emails
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-4 p-5">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-300">
          <MessageSquareText className="h-4 w-4 text-cyan-200" aria-hidden="true" />
          Template body
        </div>
        <pre className="max-h-72 overflow-auto whitespace-pre-wrap rounded-2xl border border-white/10 bg-black/25 p-4 text-sm leading-6 text-slate-200">
          {template.body_template}
        </pre>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap gap-2">
            {template.placeholders?.slice(0, 6).map((placeholder) => (
              <span
                key={placeholder}
                className="rounded-full bg-cyan-300/10 px-2.5 py-1 text-xs font-medium text-cyan-100"
              >
                {"{"}
                {placeholder}
                {"}"}
              </span>
            ))}
          </div>
          <button
            type="button"
            onClick={() => navigator.clipboard?.writeText(template.body_template)}
            className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-xs font-medium text-slate-300 transition hover:border-white/20 hover:text-white focus:outline-none focus:ring-2 focus:ring-cyan-300/60"
          >
            <Copy className="h-3.5 w-3.5" aria-hidden="true" />
            Copy
          </button>
        </div>
      </div>
    </motion.article>
  );
}
