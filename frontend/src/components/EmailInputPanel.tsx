import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { AlertCircle, MailCheck, SendHorizontal, Sparkles } from "lucide-react";
import type { GenerateTemplateResponse } from "../types/api";
import { SAMPLE_EMAIL } from "../utils/constants";
import { LoadingState } from "./LoadingState";
import { TemplateCard } from "./TemplateCard";

interface EmailInputPanelProps {
  loading?: boolean;
  result: GenerateTemplateResponse | null;
  error?: string | null;
  onGenerate: (subject: string, body: string, topK: number) => void;
}

export function EmailInputPanel({ loading = false, result, error, onGenerate }: EmailInputPanelProps) {
  const [subject, setSubject] = useState("Following up on the migration project");
  const [body, setBody] = useState(SAMPLE_EMAIL);
  const [topK, setTopK] = useState(1);

  const trimmedBody = body.trim();
  const wordCount = useMemo(() => (trimmedBody ? trimmedBody.split(/\s+/).length : 0), [trimmedBody]);
  const canSubmit = !loading && trimmedBody.length > 0;

  function handleSubmit() {
    if (!canSubmit) return;
    onGenerate(subject, body, topK);
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      handleSubmit();
    }
  }

  return (
    <section className="section-shell" id="generate">
      <div className="section-heading">
        <p className="section-kicker">Raw email match</p>
        <h2>Generate from a raw email</h2>
        <p>
          Paste an email and the backend will return the closest generated template plus detected tone and
          sentiment.
        </p>
      </div>

      <div className="grid gap-5 lg:grid-cols-[0.95fr_1.05fr]">
        <motion.div
          className="glass-card flex flex-col p-6"
          initial={{ opacity: 0, y: 18 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 0.45 }}
          whileHover={{ y: -2 }}
        >
          <div className="mb-5 flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-violet-500 to-blue-500 text-white shadow-glow-violet">
              <MailCheck className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <h3 className="text-lg font-semibold tracking-tight text-white">Email input</h3>
              <p className="text-sm text-slate-400">Subject is optional. Body is required.</p>
            </div>
          </div>

          <label className="block text-sm font-medium text-slate-200" htmlFor="email-subject">
            Subject
          </label>
          <input
            id="email-subject"
            value={subject}
            onChange={(event) => setSubject(event.target.value)}
            className="input-shell mt-2 w-full"
            placeholder="Optional subject line"
          />

          <label className="mt-5 block text-sm font-medium text-slate-200" htmlFor="email-body">
            Raw email body
          </label>
          <textarea
            id="email-body"
            value={body}
            onChange={(event) => setBody(event.target.value)}
            onKeyDown={handleKeyDown}
            className="input-shell mt-2 min-h-[260px] w-full resize-y leading-7 font-sans"
            placeholder="Paste a customer follow-up, request, complaint, confirmation, or apology email..."
            aria-describedby="email-body-help"
          />
          <p id="email-body-help" className="mt-2 flex items-center justify-between text-xs text-slate-500">
            <span>
              {wordCount} {wordCount === 1 ? "word" : "words"} &middot; {trimmedBody.length} chars
            </span>
            <span className="hidden sm:inline">
              Press <span className="kbd">Cmd</span> <span className="kbd">Enter</span> to match
            </span>
          </p>

          <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <label className="flex items-center gap-3 text-sm text-slate-300">
              <span>Matches</span>
              <select
                value={topK}
                onChange={(event) => setTopK(Number(event.target.value))}
                className="input-shell w-24 py-2"
                aria-label="Number of matches"
              >
                {[1, 2, 3, 4, 5].map((count) => (
                  <option key={count} value={count}>
                    {count}
                  </option>
                ))}
              </select>
            </label>

            <motion.button
              type="button"
              onClick={handleSubmit}
              disabled={!canSubmit}
              whileTap={canSubmit ? { scale: 0.98 } : undefined}
              className="premium-button"
            >
              {loading ? (
                <LoadingState label="Matching..." />
              ) : (
                <>
                  <span>Find matching template</span>
                  <SendHorizontal className="h-4 w-4" aria-hidden="true" />
                </>
              )}
            </motion.button>
          </div>

          <AnimatePresence>
            {error ? (
              <motion.p
                key="generate-error"
                className="mt-4 flex items-start gap-2 rounded-2xl border border-rose-300/20 bg-rose-300/[0.08] px-4 py-3 text-sm text-rose-200"
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.25 }}
                role="alert"
              >
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
                <span>{error}</span>
              </motion.p>
            ) : null}
          </AnimatePresence>
        </motion.div>

        <div className="space-y-4">
          <AnimatePresence mode="wait">
            {!result ? (
              <motion.div
                key="result-empty"
                className="glass-card flex min-h-full flex-col justify-center p-8"
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -14 }}
                transition={{ duration: 0.4 }}
              >
                <div className="mb-5 inline-flex w-fit items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/[0.08] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.24em] text-cyan-100">
                  <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
                  Result preview
                </div>
                <h3 className="text-2xl font-semibold tracking-tight text-white sm:text-3xl">
                  Your best matching template will appear here.
                </h3>
                <p className="mt-3 max-w-md text-sm leading-7 text-slate-400">
                  Run the pipeline first so the backend has templates in memory, then match a raw email
                  against the generated template library.
                </p>
              </motion.div>
            ) : (
              <motion.div
                key="result-data"
                className="space-y-4"
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -14 }}
                transition={{ duration: 0.4 }}
              >
                <div className="glass-card grid grid-cols-2 gap-4 p-5">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">
                      Detected tone
                    </p>
                    <p className="mt-1.5 text-lg font-semibold capitalize text-white">
                      {result.detected_tone ?? "unknown"}
                    </p>
                  </div>
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">
                      Detected sentiment
                    </p>
                    <p className="mt-1.5 text-lg font-semibold capitalize text-white">
                      {result.detected_sentiment ?? "unknown"}
                    </p>
                  </div>
                </div>

                {result.matches.map((match, index) => (
                  <motion.div
                    key={match.template.template_id}
                    className="space-y-3"
                    initial={{ opacity: 0, y: 14 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: index * 0.06 }}
                  >
                    <div className="inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/[0.08] px-3 py-1 text-xs font-medium text-cyan-100">
                      <span className="h-1.5 w-1.5 rounded-full bg-cyan-300 shadow-[0_0_10px_rgba(34,211,238,0.8)]" />
                      Similarity {(match.similarity * 100).toFixed(1)}%
                    </div>
                    <TemplateCard template={match.template} index={index} />
                  </motion.div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
}
