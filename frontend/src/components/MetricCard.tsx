import { motion } from "motion/react";
import type { LucideIcon } from "lucide-react";

interface MetricCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  helper?: string;
}

export function MetricCard({ icon: Icon, label, value, helper }: MetricCardProps) {
  return (
    <motion.div
      className="glass-card group relative overflow-hidden p-6"
      initial={{ opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ y: -4 }}
    >
      <div
        className="pointer-events-none absolute -right-16 -top-16 h-40 w-40 rounded-full bg-cyan-400/10 blur-3xl transition-opacity duration-500 group-hover:bg-cyan-400/20"
        aria-hidden="true"
      />
      <div className="relative flex items-center justify-between gap-4">
        <div className="grid h-11 w-11 place-items-center rounded-2xl border border-white/10 bg-white/[0.07] text-cyan-200 shadow-inner-soft">
          <Icon className="h-5 w-5" aria-hidden="true" />
        </div>
        <span className="h-2 w-2 animate-pulse-soft rounded-full bg-cyan-300 shadow-[0_0_18px_rgba(34,211,238,0.8)]" aria-hidden="true" />
      </div>
      <p className="relative mt-6 text-3xl font-semibold tracking-tightest text-white sm:text-[2rem]">
        {value}
      </p>
      <p className="relative mt-1 text-sm font-medium text-slate-200">{label}</p>
      {helper ? <p className="relative mt-2 text-xs leading-5 text-slate-500">{helper}</p> : null}
    </motion.div>
  );
}
