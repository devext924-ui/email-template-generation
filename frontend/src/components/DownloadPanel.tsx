import { motion } from "motion/react";
import { Download, FileJson, FileSpreadsheet, FileText } from "lucide-react";
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
        <p>Export generated templates in formats that work for analysis, APIs, and docs.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {DOWNLOADS.map((item) => {
          const Icon = icons[item.format];
          const isLoading = loadingFormat === item.format;
          return (
            <motion.button
              key={item.format}
              type="button"
              onClick={() => onDownload(item.format, item.filename)}
              className="glass-card flex items-center justify-between p-5 text-left transition hover:border-cyan-300/30 focus:outline-none focus:ring-2 focus:ring-cyan-300/60"
              whileHover={{ y: -4, scale: 1.01 }}
              whileTap={{ scale: 0.98 }}
            >
              <span className="flex items-center gap-4">
                <span className="grid h-12 w-12 place-items-center rounded-2xl bg-white/[0.08] text-cyan-200">
                  <Icon className="h-5 w-5" aria-hidden="true" />
                </span>
                <span>
                  <span className="block font-semibold text-white">{item.label}</span>
                  <span className="mt-1 block text-sm text-slate-500">{item.filename}</span>
                </span>
              </span>
              <Download
                className={`h-5 w-5 text-slate-400 ${isLoading ? "animate-bounce" : ""}`}
                aria-hidden="true"
              />
            </motion.button>
          );
        })}
      </div>
      {error ? (
        <p className="mt-4 rounded-2xl border border-amber-300/20 bg-amber-300/10 px-4 py-3 text-sm text-amber-100">
          {error}
        </p>
      ) : null}
    </section>
  );
}
