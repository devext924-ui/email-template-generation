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
      className="glass-card p-5"
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.42 }}
      whileHover={{ y: -3 }}
    >
      <div className="flex items-center justify-between gap-4">
        <div className="grid h-10 w-10 place-items-center rounded-2xl bg-white/[0.08] text-cyan-200">
          <Icon className="h-5 w-5" aria-hidden="true" />
        </div>
        <span className="h-2 w-2 rounded-full bg-cyan-300 shadow-[0_0_18px_rgba(34,211,238,0.8)]" />
      </div>
      <p className="mt-5 text-3xl font-semibold tracking-tight text-white">{value}</p>
      <p className="mt-1 text-sm font-medium text-slate-300">{label}</p>
      {helper ? <p className="mt-2 text-xs leading-5 text-slate-500">{helper}</p> : null}
    </motion.div>
  );
}
