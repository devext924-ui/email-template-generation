import { useEffect, useState } from "react";
import { motion } from "motion/react";
import {
  Brain,
  CheckCircle2,
  GaugeCircle,
  Rocket,
  SlidersHorizontal,
  Sparkles,
} from "lucide-react";
import { apiClient, ApiClientError } from "./api/client";
import { ActionCard } from "./components/ActionCard";
import { DownloadPanel } from "./components/DownloadPanel";
import { EmailInputPanel } from "./components/EmailInputPanel";
import { EvaluationPanel } from "./components/EvaluationPanel";
import { HeroSection } from "./components/HeroSection";
import { Navbar } from "./components/Navbar";
import { TemplateBrowser } from "./components/TemplateBrowser";
import { UploadPanel } from "./components/UploadPanel";
import type {
  EvaluationResponse,
  FineTuneResponse,
  GenerateTemplateResponse,
  HealthResponse,
  PipelineRequest,
  PipelineResponse,
  TemplateOut,
  UploadResponse,
} from "./types/api";
import { CLUSTERING_METHODS, fadeUp } from "./utils/constants";

type LoadingKey = "health" | "upload" | "pipeline" | "fineTune" | "generate" | "download";

interface Notice {
  type: "success" | "error" | "info";
  message: string;
}

const initialLoading: Record<LoadingKey, boolean> = {
  health: false,
  upload: false,
  pipeline: false,
  fineTune: false,
  generate: false,
  download: false,
};

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [pipelineResult, setPipelineResult] = useState<PipelineResponse | null>(null);
  const [fineTuneResult, setFineTuneResult] = useState<FineTuneResponse | null>(null);
  const [templates, setTemplates] = useState<TemplateOut[]>([]);
  const [evaluation, setEvaluation] = useState<EvaluationResponse | null>(null);
  const [matchResult, setMatchResult] = useState<GenerateTemplateResponse | null>(null);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [generateError, setGenerateError] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(initialLoading);

  const [clusteringMethod, setClusteringMethod] =
    useState<(typeof CLUSTERING_METHODS)[number]>("kmeans");
  const [useFineTuned, setUseFineTuned] = useState(false);
  const [autoClusters, setAutoClusters] = useState(true);
  const [nClusters, setNClusters] = useState(10);
  const [epochs, setEpochs] = useState(1);
  const [batchSize, setBatchSize] = useState(16);
  const [usePseudoLabels, setUsePseudoLabels] = useState(true);
  const [loadingDownloadFormat, setLoadingDownloadFormat] = useState<string | null>(null);

  const backendOnline = health?.status === "ok";
  const uploadedCsvPath = uploadResult?.saved_path ?? null;

  useEffect(() => {
    void refreshHealth();
    void refreshArtifacts(true);
  }, []);

  async function withLoading<T>(key: LoadingKey, action: () => Promise<T>): Promise<T> {
    setLoading((current) => ({ ...current, [key]: true }));
    try {
      return await action();
    } finally {
      setLoading((current) => ({ ...current, [key]: false }));
    }
  }

  async function refreshHealth() {
    await withLoading("health", async () => {
      try {
        const response = await apiClient.health();
        setHealth(response);
        setHealthError(null);
      } catch (error) {
        setHealth(null);
        setHealthError(error instanceof Error ? error.message : "Backend health check failed.");
      }
    });
  }

  async function refreshArtifacts(silent = false) {
    try {
      const [templateResponse, metricsResponse] = await Promise.all([
        apiClient.templates(),
        apiClient.evaluation(),
      ]);
      setTemplates(templateResponse.templates);
      setEvaluation(metricsResponse);
    } catch (error) {
      if (!silent) {
        setNotice({
          type: "info",
          message:
            error instanceof Error
              ? error.message
              : "Run the pipeline to populate templates and metrics.",
        });
      }
    }
  }

  function handleSelectFile(file: File | null) {
    setSelectedFile(file);
    setUploadError(null);
    if (file) {
      setUploadResult(null);
    }
  }

  async function handleUpload() {
    if (!selectedFile) return;
    setUploadError(null);
    setNotice(null);
    await withLoading("upload", async () => {
      try {
        const response = await apiClient.uploadCsv(selectedFile);
        setUploadResult(response);
        setNotice({
          type: "success",
          message: `Uploaded ${response.filename} with ${response.rows.toLocaleString()} rows.`,
        });
        await refreshHealth();
      } catch (error) {
        const message = friendlyError(error);
        setUploadError(message);
        setNotice({ type: "error", message });
      }
    });
  }

  async function handleRunPipeline() {
    setNotice(null);
    const payload: PipelineRequest = {
      csv_path: uploadedCsvPath,
      use_fine_tuned: useFineTuned,
      n_clusters: autoClusters ? null : nClusters,
      clustering_method: clusteringMethod,
    };

    await withLoading("pipeline", async () => {
      try {
        const response = await apiClient.runPipeline(payload);
        setPipelineResult(response);
        setEvaluation(response.evaluation);
        const templateResponse = await apiClient.templates();
        setTemplates(templateResponse.templates);
        setNotice({
          type: "success",
          message: `Pipeline completed: ${response.n_templates} templates from ${response.n_emails.toLocaleString()} emails.`,
        });
        await refreshHealth();
      } catch (error) {
        setNotice({ type: "error", message: friendlyError(error) });
      }
    });
  }

  async function handleFineTune() {
    setNotice(null);
    await withLoading("fineTune", async () => {
      try {
        const response = await apiClient.fineTune({
          csv_path: uploadedCsvPath,
          epochs,
          batch_size: batchSize,
          use_pseudo_labels: usePseudoLabels,
        });
        setFineTuneResult(response);
        setNotice({
          type: "success",
          message: `Fine-tuned model saved after ${response.n_pairs.toLocaleString()} training pairs.`,
        });
      } catch (error) {
        setNotice({ type: "error", message: friendlyError(error) });
      }
    });
  }

  async function handleGenerate(subject: string, body: string, topK: number) {
    setGenerateError(null);
    await withLoading("generate", async () => {
      try {
        const response = await apiClient.generateTemplate({ subject, body, top_k: topK });
        setMatchResult(response);
      } catch (error) {
        setGenerateError(friendlyError(error));
      }
    });
  }

  async function handleDownload(format: "csv" | "json" | "markdown", filename: string) {
    setDownloadError(null);
    setLoadingDownloadFormat(format);
    await withLoading("download", async () => {
      try {
        const blob = await apiClient.downloadOutput(format);
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
      } catch (error) {
        setDownloadError(
          `${friendlyError(error)} If outputs are not ready, run the pipeline first.`,
        );
      } finally {
        setLoadingDownloadFormat(null);
      }
    });
  }

  return (
    <div className="min-h-screen overflow-hidden bg-[#09090B] text-slate-100">
      <div className="pointer-events-none fixed inset-0 bg-hero-grid bg-[length:48px_48px] opacity-[0.08]" />
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.18),transparent_34rem),radial-gradient(circle_at_20%_30%,rgba(139,92,246,0.16),transparent_30rem),linear-gradient(180deg,#09090B_0%,#0B0F19_48%,#09090B_100%)]" />

      <div className="relative z-10">
        <Navbar health={health} healthError={healthError} apiBaseUrl={apiClient.baseUrl} />
        <HeroSection
          templateCount={templates.length || health?.n_templates || 0}
          emailCount={evaluation?.n_emails || health?.n_emails_loaded || 0}
        />

        <main className="mx-auto max-w-7xl space-y-16 px-4 pb-20 sm:px-6 lg:px-8">
          {notice ? <NoticeBanner notice={notice} /> : null}

          <motion.section
            id="actions"
            className="section-shell"
            initial={fadeUp.initial}
            whileInView={fadeUp.animate}
            viewport={{ once: true, margin: "-80px" }}
            transition={fadeUp.transition}
          >
            <div className="section-heading">
              <p className="section-kicker">Control center</p>
              <h2>Main action grid</h2>
              <p>Upload data, run the NLP pipeline, fine-tune embeddings, and test matching.</p>
            </div>

            <div className="grid grid-cols-1 gap-5 lg:grid-cols-4">
              <UploadPanel
                selectedFile={selectedFile}
                uploadResult={uploadResult}
                loading={loading.upload}
                error={uploadError}
                onSelectFile={handleSelectFile}
                onUpload={handleUpload}
              />

              <ActionCard
                icon={Rocket}
                title="Run Pipeline"
                eyebrow={uploadedCsvPath ? "Uploaded CSV" : "Sample fallback"}
                description="Trigger preprocessing, embeddings, clustering, template generation, and evaluation."
                buttonLabel={loading.pipeline ? "Running..." : "Run pipeline"}
                loading={loading.pipeline}
                disabled={!backendOnline}
                onAction={handleRunPipeline}
                tone="blue"
              >
                <select
                  value={clusteringMethod}
                  onChange={(event) =>
                    setClusteringMethod(event.target.value as (typeof CLUSTERING_METHODS)[number])
                  }
                  className="input-shell w-full"
                >
                  {CLUSTERING_METHODS.map((method) => (
                    <option key={method} value={method}>
                      {method}
                    </option>
                  ))}
                </select>
                <label className="flex items-center justify-between gap-3 text-sm text-slate-300">
                  Auto clusters
                  <input
                    type="checkbox"
                    checked={autoClusters}
                    onChange={(event) => setAutoClusters(event.target.checked)}
                    className="h-4 w-4 rounded border-white/20 bg-white/10 text-cyan-400 focus:ring-cyan-300"
                  />
                </label>
                {!autoClusters ? (
                  <input
                    type="number"
                    min={2}
                    max={100}
                    value={nClusters}
                    onChange={(event) => setNClusters(Number(event.target.value))}
                    className="input-shell w-full"
                    aria-label="Number of clusters"
                  />
                ) : null}
                <label className="flex items-center justify-between gap-3 text-sm text-slate-300">
                  Use fine-tuned model
                  <input
                    type="checkbox"
                    checked={useFineTuned}
                    onChange={(event) => setUseFineTuned(event.target.checked)}
                    className="h-4 w-4 rounded border-white/20 bg-white/10 text-cyan-400 focus:ring-cyan-300"
                  />
                </label>
              </ActionCard>

              <ActionCard
                icon={Brain}
                title="Fine-Tune Model"
                eyebrow="Optional"
                description="Improve semantic clustering with labeled or weakly supervised email pairs."
                buttonLabel={loading.fineTune ? "Fine-tuning..." : "Fine-tune"}
                loading={loading.fineTune}
                disabled={!backendOnline}
                onAction={handleFineTune}
                tone="violet"
              >
                <div className="grid grid-cols-2 gap-3">
                  <label className="text-xs font-medium text-slate-400">
                    Epochs
                    <input
                      type="number"
                      min={1}
                      max={10}
                      value={epochs}
                      onChange={(event) => setEpochs(Number(event.target.value))}
                      className="input-shell mt-1 w-full"
                    />
                  </label>
                  <label className="text-xs font-medium text-slate-400">
                    Batch
                    <input
                      type="number"
                      min={2}
                      max={128}
                      value={batchSize}
                      onChange={(event) => setBatchSize(Number(event.target.value))}
                      className="input-shell mt-1 w-full"
                    />
                  </label>
                </div>
                <label className="flex items-center justify-between gap-3 text-sm text-slate-300">
                  Pseudo-labels
                  <input
                    type="checkbox"
                    checked={usePseudoLabels}
                    onChange={(event) => setUsePseudoLabels(event.target.checked)}
                    className="h-4 w-4 rounded border-white/20 bg-white/10 text-violet-400 focus:ring-violet-300"
                  />
                </label>
                {fineTuneResult ? (
                  <p className="rounded-2xl border border-emerald-300/20 bg-emerald-300/10 p-3 text-xs leading-5 text-emerald-100">
                    Model ready: {fineTuneResult.n_pairs.toLocaleString()} pairs,{" "}
                    {fineTuneResult.duration_seconds.toFixed(1)}s.
                  </p>
                ) : null}
              </ActionCard>

              <ActionCard
                icon={SlidersHorizontal}
                title="Generate Template"
                eyebrow="Inference"
                description="Jump to raw email matching and retrieve the closest template from backend state."
                buttonLabel="Open generator"
                disabled={!backendOnline}
                onAction={() => document.getElementById("generate")?.scrollIntoView({ behavior: "smooth" })}
                tone="cyan"
              />
            </div>
          </motion.section>

          <EvaluationPanel evaluation={evaluation} pipelineResult={pipelineResult} />
          <TemplateBrowser templates={templates} onRunPipeline={handleRunPipeline} />
          <EmailInputPanel
            loading={loading.generate}
            result={matchResult}
            error={generateError}
            onGenerate={handleGenerate}
          />
          <DownloadPanel
            loadingFormat={loadingDownloadFormat}
            error={downloadError}
            onDownload={handleDownload}
          />
        </main>
      </div>
    </div>
  );
}

function NoticeBanner({ notice }: { notice: Notice }) {
  const styles = {
    success: "border-emerald-300/20 bg-emerald-300/10 text-emerald-100",
    error: "border-rose-300/20 bg-rose-300/10 text-rose-100",
    info: "border-cyan-300/20 bg-cyan-300/10 text-cyan-100",
  };

  return (
    <motion.div
      className={`flex items-center gap-3 rounded-3xl border px-5 py-4 text-sm shadow-card ${styles[notice.type]}`}
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      role={notice.type === "error" ? "alert" : "status"}
    >
      {notice.type === "success" ? (
        <CheckCircle2 className="h-5 w-5 shrink-0" aria-hidden="true" />
      ) : notice.type === "error" ? (
        <GaugeCircle className="h-5 w-5 shrink-0" aria-hidden="true" />
      ) : (
        <Sparkles className="h-5 w-5 shrink-0" aria-hidden="true" />
      )}
      <span>{notice.message}</span>
    </motion.div>
  );
}

function friendlyError(error: unknown) {
  if (error instanceof ApiClientError || error instanceof Error) {
    return error.message;
  }
  return "Something went wrong. Please try again.";
}

export default App;
