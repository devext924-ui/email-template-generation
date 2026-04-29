import type { ReactNode } from "react";
import { motion } from "motion/react";
import type { LucideIcon } from "lucide-react";
import { ArrowRight, Loader2 } from "lucide-react";

interface ActionCardProps {
  icon: LucideIcon;
  title: string;
  eyebrow?: string;
  description: string;
  buttonLabel: string;
  onAction: () => void;
  loading?: boolean;
  disabled?: boolean;
  children?: ReactNode;
  tone?: "blue" | "violet" | "cyan";
}

const toneClasses = {
  blue: "from-blue-500 to-cyan-400 shadow-blue-500/25",
  violet: "from-violet-500 to-fuchsia-400 shadow-violet-500/25",
  cyan: "from-cyan-400 to-emerald-300 shadow-cyan-500/25",
};

export function ActionCard({
  icon: Icon,
  title,
  eyebrow,
  description,
  buttonLabel,
  onAction,
  loading = false,
  disabled = false,
  children,
  tone = "blue",
}: ActionCardProps) {
  return (
    <motion.article
      className="glass-card group flex h-full flex-col p-6"
      whileHover={{ y: -4, scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
      transition={{ type: "spring", stiffness: 240, damping: 22 }}
    >
      <div className="flex items-start justify-between gap-4">
        <div
          className={`grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br ${toneClasses[tone]} shadow-lg`}
        >
          <Icon className="h-5 w-5 text-white" aria-hidden="true" />
        </div>
        {eyebrow ? (
          <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-slate-300">
            {eyebrow}
          </span>
        ) : null}
      </div>
      <h3 className="mt-5 text-xl font-semibold tracking-tight text-white">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-slate-400">{description}</p>
      {children ? <div className="mt-5 space-y-3">{children}</div> : null}
      <button
        type="button"
        onClick={onAction}
        disabled={disabled || loading}
        className="mt-auto flex w-full items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-sm font-semibold text-white transition hover:border-white/20 hover:bg-white/[0.15] focus:outline-none focus:ring-2 focus:ring-cyan-300/60 disabled:cursor-not-allowed disabled:opacity-45"
      >
        {loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : null}
        {buttonLabel}
        {!loading ? <ArrowRight className="h-4 w-4" aria-hidden="true" /> : null}
      </button>
    </motion.article>
  );
}
