import { motion } from "motion/react";
import { BrainCircuit } from "lucide-react";

interface FooterProps {
  apiBaseUrl: string;
}

export function Footer({ apiBaseUrl }: FooterProps) {
  const year = new Date().getFullYear();

  return (
    <motion.footer
      className="mt-24 border-t border-white/[0.06] bg-white/[0.015] backdrop-blur"
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.5 }}
    >
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-8 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-cyan-400 via-blue-500 to-violet-500 shadow-glow">
            <BrainCircuit className="h-4 w-4 text-white" aria-hidden="true" />
          </span>
          <div className="leading-tight">
            <p className="text-sm font-semibold text-white">Email Template Generation</p>
            <p className="text-xs text-slate-500">NLP workbench &middot; built with FastAPI + React</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
          <span>&copy; {year} NLP Workbench</span>
          <span className="hidden h-1 w-1 rounded-full bg-slate-700 sm:inline-block" aria-hidden="true" />
          <span className="font-mono text-slate-400">{apiBaseUrl}</span>
        </div>
      </div>
    </motion.footer>
  );
}
