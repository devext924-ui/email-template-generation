import { useState } from "react";
import { motion } from "motion/react";
import { Activity, BrainCircuit, Check, Copy, Github } from "lucide-react";
import type { HealthResponse } from "../types/api";

interface NavbarProps {
  health: HealthResponse | null;
  healthError?: string | null;
  apiBaseUrl: string;
}

export function Navbar({ health, healthError, apiBaseUrl }: NavbarProps) {
  const isOnline = health?.status === "ok";
  const [copied, setCopied] = useState(false);

  function copyApiUrl() {
    if (!navigator.clipboard) return;
    void navigator.clipboard.writeText(apiBaseUrl).then(() => {
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1400);
    });
  }

  return (
    <motion.header
      className="sticky top-0 z-40 border-b border-white/[0.08] bg-[#05070A]/75 backdrop-blur-2xl"
      initial={{ opacity: 0, y: -14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
    >
      <nav className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <a href="#top" className="group flex items-center gap-3" aria-label="Email Template Generation home">
          <span className="relative grid h-10 w-10 place-items-center overflow-hidden rounded-2xl bg-gradient-to-br from-cyan-400 via-blue-500 to-violet-500 shadow-glow">
            <BrainCircuit className="h-5 w-5 text-white" aria-hidden="true" />
            <span
              className="pointer-events-none absolute inset-0 rounded-2xl bg-gradient-to-b from-white/30 to-transparent opacity-50"
              aria-hidden="true"
            />
          </span>
          <span className="hidden flex-col leading-tight sm:flex">
            <span className="text-[10px] font-semibold uppercase tracking-[0.34em] text-slate-500 group-hover:text-slate-400">
              NLP Workbench
            </span>
            <span className="text-base font-semibold tracking-tight text-white">
              Email Template Generation
            </span>
          </span>
          <span className="text-base font-semibold tracking-tight text-white sm:hidden">
            Email Templates
          </span>
        </a>

        <div className="flex items-center gap-2 sm:gap-3">
          <button
            type="button"
            onClick={copyApiUrl}
            className="hidden items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.04] px-3.5 py-1.5 text-xs text-slate-400 transition hover:border-white/20 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/60 lg:inline-flex"
            title={`Copy API base URL: ${apiBaseUrl}`}
          >
            <span className="text-slate-500">API</span>
            <span className="font-mono text-slate-200">{apiBaseUrl}</span>
            {copied ? (
              <Check className="h-3.5 w-3.5 text-emerald-300" aria-hidden="true" />
            ) : (
              <Copy className="h-3.5 w-3.5 text-slate-500" aria-hidden="true" />
            )}
          </button>

          <div
            className="flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.04] px-3 py-1.5 text-xs sm:px-4 sm:py-2 sm:text-sm"
            title={healthError ?? health?.embedding_model ?? "Backend status"}
            role="status"
            aria-live="polite"
          >
            <span className="relative flex h-2.5 w-2.5">
              <span
                className={`absolute inline-flex h-full w-full rounded-full ${
                  isOnline ? "animate-ping bg-emerald-400/70" : "bg-rose-400/0"
                }`}
                aria-hidden="true"
              />
              <span
                className={`relative inline-flex h-2.5 w-2.5 rounded-full ${
                  isOnline
                    ? "bg-emerald-400 shadow-[0_0_18px_rgba(52,211,153,0.85)]"
                    : "bg-rose-400 shadow-[0_0_14px_rgba(244,114,128,0.7)]"
                }`}
              />
            </span>
            <Activity className="hidden h-4 w-4 text-slate-500 sm:block" aria-hidden="true" />
            <span className={isOnline ? "text-emerald-200" : "text-rose-200"}>
              {isOnline ? "Backend online" : "Backend offline"}
            </span>
          </div>

          <a
            href="https://github.com/"
            className="hidden items-center justify-center rounded-full border border-white/[0.08] bg-white/[0.04] p-2 text-slate-300 transition hover:border-white/20 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/60 sm:inline-flex"
            aria-label="Project repository"
            target="_blank"
            rel="noreferrer"
          >
            <Github className="h-4 w-4" aria-hidden="true" />
          </a>
        </div>
      </nav>
    </motion.header>
  );
}
