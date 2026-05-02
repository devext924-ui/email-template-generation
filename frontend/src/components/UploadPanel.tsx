import { useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import {
  AlertCircle,
  CheckCircle2,
  FileSpreadsheet,
  FileUp,
  Loader2,
  UploadCloud,
} from "lucide-react";
import type { UploadResponse } from "../types/api";

interface UploadPanelProps {
  selectedFile: File | null;
  uploadResult: UploadResponse | null;
  loading?: boolean;
  error?: string | null;
  onSelectFile: (file: File | null) => void;
  onUpload: () => void;
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
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
  const [dragActive, setDragActive] = useState(false);

  function handleDrop(event: React.DragEvent<HTMLButtonElement>) {
    event.preventDefault();
    setDragActive(false);
    const file = event.dataTransfer.files?.[0];
    if (file) onSelectFile(file);
  }

  return (
    <motion.article
      className="glass-card group relative flex h-full flex-col overflow-hidden p-6"
      initial={{ opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ y: -4 }}
    >
      <div
        className="pointer-events-none absolute -right-20 -top-20 h-44 w-44 rounded-full bg-cyan-400/10 blur-3xl transition-opacity duration-500 group-hover:bg-cyan-400/20"
        aria-hidden="true"
      />

      <div className="relative flex items-start justify-between gap-4">
        <div className="grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-cyan-400 to-blue-500 shadow-lg shadow-cyan-500/30">
          <UploadCloud className="h-5 w-5 text-white" aria-hidden="true" />
        </div>
        {uploadResult ? (
          <span className="badge-success">
            <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
            Uploaded
          </span>
        ) : (
          <span className="badge whitespace-nowrap">Step 1</span>
        )}
      </div>

      <h3 className="relative mt-5 text-xl font-semibold tracking-tight text-white">Upload Dataset</h3>
      <p className="relative mt-2 text-sm leading-6 text-slate-400">
        Add an email dataset with{" "}
        <span className="font-medium text-slate-200">email_id</span>,{" "}
        <span className="font-medium text-slate-200">subject</span>, and{" "}
        <span className="font-medium text-slate-200">body</span> columns.
      </p>

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragOver={(event) => {
          event.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        className={`relative mt-5 flex w-full items-center justify-between gap-3 rounded-2xl border border-dashed px-4 py-4 text-left transition focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/60 ${
          dragActive
            ? "border-cyan-300/60 bg-cyan-300/[0.08]"
            : selectedFile
              ? "border-cyan-300/30 bg-cyan-300/[0.04] hover:border-cyan-300/50"
              : "border-white/15 bg-white/[0.03] hover:border-cyan-300/50 hover:bg-cyan-300/[0.04]"
        }`}
        aria-label={selectedFile ? `Selected file ${selectedFile.name}. Click to change.` : "Choose a CSV file"}
      >
        <span className="flex min-w-0 items-center gap-3">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-white/10 bg-white/[0.06] text-cyan-200">
            {selectedFile ? (
              <FileSpreadsheet className="h-4 w-4" aria-hidden="true" />
            ) : (
              <FileUp className="h-4 w-4" aria-hidden="true" />
            )}
          </span>
          <span className="min-w-0">
            <span className="block truncate text-sm font-semibold text-white">
              {selectedFile?.name ?? (dragActive ? "Drop CSV to upload" : "Choose or drop a CSV file")}
            </span>
            <span className="mt-0.5 block text-xs text-slate-500">
              {selectedFile ? formatFileSize(selectedFile.size) : "CSV only · drag & drop supported"}
            </span>
          </span>
        </span>
      </button>

      <input
        ref={inputRef}
        type="file"
        accept=".csv,text/csv"
        className="sr-only"
        aria-hidden="true"
        tabIndex={-1}
        onChange={(event) => onSelectFile(event.target.files?.[0] ?? null)}
      />

      <div className="relative mt-3 min-h-[1.5rem] text-sm">
        <AnimatePresence mode="wait">
          {error ? (
            <motion.p
              key="error"
              className="flex items-start gap-2 text-rose-300"
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.25 }}
              role="alert"
            >
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <span>{error}</span>
            </motion.p>
          ) : uploadResult ? (
            <motion.p
              key="ok"
              className="flex items-start gap-2 text-emerald-200"
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.25 }}
            >
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <span>
                {uploadResult.filename} validated &middot;{" "}
                <span className="font-semibold">{uploadResult.rows.toLocaleString()}</span> rows
              </span>
            </motion.p>
          ) : null}
        </AnimatePresence>
      </div>

      <motion.button
        type="button"
        onClick={onUpload}
        disabled={!selectedFile || loading}
        whileTap={!loading && selectedFile ? { scale: 0.98 } : undefined}
        className="relative mt-auto flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-cyan-400 to-blue-500 px-4 py-3 text-sm font-semibold text-white shadow-glow-cyan transition hover:brightness-110 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/70 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            <span>Uploading...</span>
          </>
        ) : (
          <>
            <UploadCloud className="h-4 w-4" aria-hidden="true" />
            <span>Upload dataset</span>
          </>
        )}
      </motion.button>
    </motion.article>
  );
}
