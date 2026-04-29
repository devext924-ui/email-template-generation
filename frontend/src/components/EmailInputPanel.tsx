import { useState } from "react";
import { motion } from "motion/react";
import { MailCheck, SendHorizontal } from "lucide-react";
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

  return (
    <section className="section-shell" id="generate">
      <div className="section-heading">
        <p className="section-kicker">Raw email match</p>
        <h2>Generate from a raw email</h2>
        <p>
          Paste an email and the backend will return the closest generated template plus detected tone.
        </p>
      </div>

      <div className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
        <motion.div className="glass-card p-6" whileHover={{ y: -3 }}>
          <div className="mb-5 flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-violet-500 to-blue-500 text-white shadow-lg shadow-violet-500/25">
              <MailCheck className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <h3 className="font-semibold text-white">Email input</h3>
              <p className="text-sm text-slate-400">Subject is optional. Body is required.</p>
            </div>
          </div>

          <label className="block text-sm font-medium text-slate-300" htmlFor="email-subject">
            Subject
          </label>
          <input
            id="email-subject"
            value={subject}
            onChange={(event) => setSubject(event.target.value)}
            className="input-shell mt-2 w-full"
            placeholder="Optional subject"
          />

          <label className="mt-5 block text-sm font-medium text-slate-300" htmlFor="email-body">
            Raw email body
          </label>
          <textarea
            id="email-body"
            value={body}
            onChange={(event) => setBody(event.target.value)}
            className="input-shell mt-2 min-h-[260px] w-full resize-y leading-6"
            placeholder="Paste a customer follow-up, request, complaint, confirmation, or apology email..."
          />

          <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <label className="flex items-center gap-3 text-sm text-slate-300">
              Matches
              <select
                value={topK}
                onChange={(event) => setTopK(Number(event.target.value))}
                className="input-shell w-24"
              >
                {[1, 2, 3, 4, 5].map((count) => (
                  <option key={count} value={count}>
                    {count}
                  </option>
                ))}
              </select>
            </label>

            <button
              type="button"
              onClick={() => onGenerate(subject, body, topK)}
              disabled={loading || !body.trim()}
              className="premium-button disabled:cursor-not-allowed disabled:opacity-45"
            >
              {loading ? <LoadingState label="Matching..." /> : "Find matching template"}
              {!loading ? <SendHorizontal className="h-4 w-4" aria-hidden="true" /> : null}
            </button>
          </div>
          {error ? <p className="mt-4 text-sm text-rose-300">{error}</p> : null}
        </motion.div>

        <div className="space-y-4">
          {!result ? (
            <div className="glass-card flex min-h-full flex-col justify-center p-8">
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-cyan-200">
                Result preview
              </p>
              <h3 className="mt-4 text-2xl font-semibold tracking-tight text-white">
                Your best matching template will appear here.
              </h3>
              <p className="mt-3 text-sm leading-6 text-slate-400">
                Run the pipeline first so the backend has templates in memory, then match a raw
                email against the generated template library.
              </p>
            </div>
          ) : (
            <>
              <div className="glass-card flex flex-wrap items-center justify-between gap-3 p-5">
                <div>
                  <p className="text-sm text-slate-400">Detected tone</p>
                  <p className="text-lg font-semibold text-white">{result.detected_tone ?? "unknown"}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">Detected sentiment</p>
                  <p className="text-lg font-semibold text-white">
                    {result.detected_sentiment ?? "unknown"}
                  </p>
                </div>
              </div>
              {result.matches.map((match, index) => (
                <div key={match.template.template_id} className="space-y-3">
                  <div className="rounded-full border border-cyan-300/20 bg-cyan-300/10 px-4 py-2 text-sm font-medium text-cyan-100">
                    Similarity {(match.similarity * 100).toFixed(1)}%
                  </div>
                  <TemplateCard template={match.template} index={index} />
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </section>
  );
}
