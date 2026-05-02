import type { ReactNode } from "react";
import { motion } from "motion/react";
import { Sparkles } from "lucide-react";
import { fadeUpSm } from "../utils/constants";

interface EmptyStateProps {
  title: string;
  description: string;
  action?: ReactNode;
  icon?: ReactNode;
}

export function EmptyState({ title, description, action, icon }: EmptyStateProps) {
  return (
    <motion.div
      className="glass-card flex min-h-[260px] flex-col items-center justify-center px-8 py-12 text-center"
      initial={fadeUpSm.initial}
      whileInView={fadeUpSm.animate}
      viewport={{ once: true, margin: "-60px" }}
      transition={fadeUpSm.transition}
    >
      <div className="relative mb-6">
        <div className="absolute inset-0 -z-10 rounded-3xl bg-cyan-400/15 blur-2xl" aria-hidden="true" />
        <div className="grid h-14 w-14 place-items-center rounded-2xl border border-white/10 bg-white/[0.06] text-cyan-200 shadow-inner-soft">
          {icon ?? <Sparkles className="h-6 w-6" aria-hidden="true" />}
        </div>
      </div>
      <h3 className="text-lg font-semibold tracking-tight text-white">{title}</h3>
      <p className="mt-2 max-w-md text-sm leading-6 text-slate-400">{description}</p>
      {action ? <div className="mt-7">{action}</div> : null}
    </motion.div>
  );
}
