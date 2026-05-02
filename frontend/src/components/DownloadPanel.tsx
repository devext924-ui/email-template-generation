import { motion } from "motion/react";
import {
  AlertTriangle,
  ArrowDownToLine,
  FileJson,
  FileSpreadsheet,
  FileText,
  Loader2,
} from "lucide-react";
import { DOWNLOADS } from "../utils/constants";

interface DownloadPanelProps {
  loadingFormat?: string | null;
  error?: string | null;
  onDownload: (format: "csv" | "json" | "markdown", filename: string) => void;
}

const icons = {
  csv: FileSpreadsheet,
  json: FileJson,
  markdown: FileText,
};

export function DownloadPanel({ loadingFormat, error, onDownload }: DownloadPanelProps) {
  return (
    <section className="section-shell" id="downloads">
      <div className="section-heading">
        <p className="section-kicker">Exports</p>
        <h2>Download generated outputs</h2>
        <p>Export generated templates in formats that work for analysis, APIs, and documentation.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {DOWNLOADS.map((item, index) => {
          const Icon = icons[item.format];
          const isLoading = loadingFormat === item.format;
          return (
            <motion.button
              key={item.format}
              type="button"
              onClick={() => onDownload(item.format, item.filename)}
              disabled={isLoading}
              className="glass-card group relative flex h-full flex-col justify-between overflow-hidden p-6 text-left transition-colors hover:border-cyan-300/30 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/60 disabled:cursor-not-allowed disabled:opacity-70"
              initial={{ opacity: 0, y: 18 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.45, delay: index * 0.06 }}
              whileHover={!isLoading ? { y: -4 } : undefined}
              whileTap={!isLoading ? { scale: 0.98 } : undefined}
              aria-label={`Download ${item.label} (${item.filename})`}
            >
              <div
                className="pointer-events-none absolute -right-20 -top-20 h-44 w-44 rounded-full bg-cyan-400/10 blur-3xl transition-opacity duration-500 group-hover:bg-cyan-400/20"
                aria-hidden="true"
              />

              <div className="relative flex items-start justify-between gap-3">
                <span className="grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-cyan-400 to-blue-500 text-white shadow-glow-cyan">
                  <Icon className="h-5 w-5" aria-hidden="true" />
                </span>
                <span className="badge whitespace-nowrap font-mono">{item.filename.split(".").pop()}</span>
              </div>

              <div className="relative mt-6">
                <p className="text-lg font-semibold tracking-tight text-white">{item.label}</p>
                <p className="mt-1.5 text-sm leading-6 text-slate-400">{item.description}</p>
              </div>

              <div className="relative mt-6 flex items-center justify-between">
                <span className="text-xs text-slate-500">{item.filename}</span>
                <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 bg-white/[0.05] text-slate-300 transition group-hover:border-cyan-300/30 group-hover:text-cyan-200">
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                  ) : (
                    <ArrowDownToLine className="h-4 w-4" aria-hidden="true" />
                  )}
                </span>
              </div>
            </motion.button>
          );
        })}
      </div>

      {error ? (
        <motion.p
          className="mt-5 flex items-start gap-2 rounded-2xl border border-amber-300/20 bg-amber-300/[0.08] px-4 py-3 text-sm leading-6 text-amber-100"
          initial={{ opacity: 0, y: -6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          role="alert"
        >
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          <span>{error}</span>
        </motion.p>
      ) : null}
    </section>
  );
}
