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

const toneClasses: Record<NonNullable<ActionCardProps["tone"]>, string> = {
  blue: "from-blue-500 to-cyan-400 shadow-blue-500/30",
  violet: "from-violet-500 to-fuchsia-400 shadow-violet-500/30",
  cyan: "from-cyan-400 to-emerald-300 shadow-cyan-500/30",
};

const toneRing: Record<NonNullable<ActionCardProps["tone"]>, string> = {
  blue: "group-hover:border-blue-300/30",
  violet: "group-hover:border-violet-300/30",
  cyan: "group-hover:border-cyan-300/30",
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
      className={`glass-card group relative flex h-full flex-col overflow-hidden p-6 transition-colors ${toneRing[tone]}`}
      initial={{ opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ y: -4 }}
    >
      <div
        className="pointer-events-none absolute -right-20 -top-20 h-44 w-44 rounded-full bg-white/[0.04] blur-3xl transition-opacity duration-500 group-hover:bg-white/[0.07]"
        aria-hidden="true"
      />

      <div className="relative flex items-start justify-between gap-4">
        <div
          className={`grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br ${toneClasses[tone]} shadow-lg`}
        >
          <Icon className="h-5 w-5 text-white" aria-hidden="true" />
        </div>
        {eyebrow ? (
          <span className="badge whitespace-nowrap">{eyebrow}</span>
        ) : null}
      </div>

      <h3 className="relative mt-5 text-xl font-semibold tracking-tight text-white">{title}</h3>
      <p className="relative mt-2 text-sm leading-6 text-slate-400">{description}</p>

      {children ? <div className="relative mt-5 space-y-3">{children}</div> : null}

      <motion.button
        type="button"
        onClick={onAction}
        disabled={disabled || loading}
        whileTap={!disabled && !loading ? { scale: 0.98 } : undefined}
        className="relative mt-6 flex w-full items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/[0.06] px-4 py-3 text-sm font-semibold text-white transition hover:border-white/25 hover:bg-white/[0.10] focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/70 disabled:cursor-not-allowed disabled:opacity-45"
      >
        {loading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin text-cyan-300" aria-hidden="true" />
            <span>{buttonLabel}</span>
          </>
        ) : (
          <>
            <span>{buttonLabel}</span>
            <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" aria-hidden="true" />
          </>
        )}
      </motion.button>
    </motion.article>
  );
}
