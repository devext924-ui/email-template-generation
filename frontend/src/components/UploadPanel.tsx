import { useRef } from "react";
import { motion } from "motion/react";
import { CheckCircle2, FileUp, UploadCloud } from "lucide-react";
import type { UploadResponse } from "../types/api";
import { LoadingState } from "./LoadingState";

interface UploadPanelProps {
  selectedFile: File | null;
  uploadResult: UploadResponse | null;
  loading?: boolean;
  error?: string | null;
  onSelectFile: (file: File | null) => void;
  onUpload: () => void;
}

export function UploadPanel({
  selectedFile,
  uploadResult,
  loading = false,
  error,
  onSelectFile,
  onUpload,
}: UploadPanelProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);

  return (
    <motion.article
      className="glass-card p-6"
      whileHover={{ y: -4, scale: 1.01 }}
      transition={{ type: "spring", stiffness: 240, damping: 22 }}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-cyan-400 to-blue-500 shadow-lg shadow-cyan-500/25">
          <UploadCloud className="h-5 w-5 text-white" aria-hidden="true" />
        </div>
        {uploadResult ? (
          <span className="inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-xs font-medium text-emerald-200">
            <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
            Uploaded
          </span>
        ) : null}
      </div>

      <h3 className="mt-5 text-xl font-semibold tracking-tight text-white">Upload CSV</h3>
      <p className="mt-2 text-sm leading-6 text-slate-400">
        Add an email dataset with <span className="text-slate-200">email_id</span>,{" "}
        <span className="text-slate-200">subject</span>, and{" "}
        <span className="text-slate-200">body</span> columns.
      </p>

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className="mt-5 flex w-full items-center justify-between rounded-2xl border border-dashed border-white/[0.15] bg-white/[0.04] px-4 py-4 text-left transition hover:border-cyan-300/50 hover:bg-cyan-300/5 focus:outline-none focus:ring-2 focus:ring-cyan-300/60"
      >
        <span>
          <span className="block text-sm font-semibold text-white">
            {selectedFile?.name ?? "Choose a CSV file"}
          </span>
          <span className="mt-1 block text-xs text-slate-500">
            {selectedFile ? `${Math.max(selectedFile.size / 1024, 1).toFixed(1)} KB` : "CSV only"}
          </span>
        </span>
        <FileUp className="h-5 w-5 text-slate-400" aria-hidden="true" />
      </button>

      <input
        ref={inputRef}
        type="file"
        accept=".csv,text/csv"
        className="sr-only"
        onChange={(event) => onSelectFile(event.target.files?.[0] ?? null)}
      />

      {error ? <p className="mt-3 text-sm text-rose-300">{error}</p> : null}
      {uploadResult ? (
        <p className="mt-3 text-sm text-emerald-200">
          {uploadResult.filename} validated with {uploadResult.rows.toLocaleString()} rows.
        </p>
      ) : null}

      <button
        type="button"
        onClick={onUpload}
        disabled={!selectedFile || loading}
        className="mt-5 flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-cyan-400 to-blue-500 px-4 py-3 text-sm font-semibold text-white shadow-glow transition hover:brightness-110 focus:outline-none focus:ring-2 focus:ring-cyan-300/70 disabled:cursor-not-allowed disabled:opacity-45"
      >
        {loading ? <LoadingState label="Uploading..." /> : "Upload dataset"}
      </button>
    </motion.article>
  );
}
