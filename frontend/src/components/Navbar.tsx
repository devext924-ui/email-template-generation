import { motion } from "motion/react";
import { Activity, BrainCircuit, Github } from "lucide-react";
import type { HealthResponse } from "../types/api";

interface NavbarProps {
  health: HealthResponse | null;
  healthError?: string | null;
  apiBaseUrl: string;
}

export function Navbar({ health, healthError, apiBaseUrl }: NavbarProps) {
  const isOnline = health?.status === "ok";

  return (
    <motion.header
      className="sticky top-0 z-40 border-b border-white/10 bg-[#09090B]/75 backdrop-blur-2xl"
      initial={{ opacity: 0, y: -14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45 }}
    >
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-2xl bg-gradient-to-br from-cyan-400 via-blue-500 to-violet-500 shadow-glow">
            <BrainCircuit className="h-5 w-5 text-white" aria-hidden="true" />
          </div>
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.28em] text-slate-400">
              NLP Workbench
            </p>
            <h1 className="text-base font-semibold text-white sm:text-lg">
              Email Template Generation
            </h1>
          </div>
        </div>

        <div className="hidden items-center gap-3 md:flex">
          <div className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-xs text-slate-300">
            API: <span className="text-slate-100">{apiBaseUrl}</span>
          </div>
          <div
            className="flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm"
            title={healthError ?? health?.embedding_model}
          >
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                isOnline ? "bg-emerald-400 shadow-[0_0_18px_rgba(52,211,153,0.8)]" : "bg-rose-400"
              }`}
            />
            <Activity className="h-4 w-4 text-slate-400" aria-hidden="true" />
            <span className={isOnline ? "text-emerald-200" : "text-rose-200"}>
              {isOnline ? "Backend online" : "Backend offline"}
            </span>
          </div>
          <a
            href="#templates"
            className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm text-slate-300 transition hover:border-white/20 hover:text-white"
          >
            Templates
          </a>
          <a
            href="https://github.com/"
            className="rounded-full border border-white/10 bg-white/[0.04] p-2 text-slate-300 transition hover:border-white/20 hover:text-white"
            aria-label="Project repository"
          >
            <Github className="h-4 w-4" aria-hidden="true" />
          </a>
        </div>
      </nav>
    </motion.header>
  );
}
