import { motion } from "motion/react";
import { ArrowRight, FileText, Mail, Sparkles, WandSparkles } from "lucide-react";
import { fadeUp } from "../utils/constants";

interface HeroSectionProps {
  templateCount: number;
  emailCount: number;
}

export function HeroSection({ templateCount, emailCount }: HeroSectionProps) {
  const stats = [
    {
      icon: Mail,
      label: "Emails loaded",
      value: emailCount ? emailCount.toLocaleString() : "Ready",
    },
    {
      icon: FileText,
      label: "Templates generated",
      value: templateCount ? templateCount.toLocaleString() : "Awaiting run",
    },
    {
      icon: Sparkles,
      label: "Output formats",
      value: "CSV / JSON / MD",
    },
  ];

  return (
    <section
      id="top"
      className="relative overflow-hidden px-4 pb-16 pt-16 sm:px-6 lg:px-8 lg:pb-24 lg:pt-24"
    >
      <motion.div
        className="pointer-events-none absolute left-1/2 top-2 h-[28rem] w-[28rem] -translate-x-1/2 rounded-full bg-cyan-500/20 blur-[140px]"
        animate={{ scale: [1, 1.14, 1], opacity: [0.45, 0.8, 0.45] }}
        transition={{ duration: 9, repeat: Infinity, ease: "easeInOut" }}
        aria-hidden="true"
      />
      <motion.div
        className="pointer-events-none absolute right-[-4rem] top-32 h-80 w-80 rounded-full bg-violet-500/20 blur-[120px]"
        animate={{ x: [0, -36, 0], y: [0, 28, 0] }}
        transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
        aria-hidden="true"
      />
      <motion.div
        className="pointer-events-none absolute left-[-3rem] top-44 h-72 w-72 rounded-full bg-blue-500/15 blur-[120px]"
        animate={{ x: [0, 30, 0], y: [0, -20, 0] }}
        transition={{ duration: 14, repeat: Infinity, ease: "easeInOut" }}
        aria-hidden="true"
      />

      <div className="relative mx-auto max-w-6xl">
        <motion.div
          className="mx-auto max-w-4xl text-center"
          initial={fadeUp.initial}
          animate={fadeUp.animate}
          transition={fadeUp.transition}
        >
          <div className="mx-auto mb-7 inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/[0.08] px-4 py-1.5 text-xs font-medium tracking-wide text-cyan-100 shadow-glow-cyan backdrop-blur">
            <WandSparkles className="h-3.5 w-3.5" aria-hidden="true" />
            <span>FastAPI &middot; Sentence-Transformers &middot; Clustering</span>
          </div>
          <h2 className="text-balance gradient-text text-5xl font-semibold leading-[1.05] tracking-tightest sm:text-6xl lg:text-[5rem]">
            Transform raw emails into reusable templates.
          </h2>
          <p className="mx-auto mt-7 max-w-2xl text-balance text-lg leading-8 text-slate-300 sm:text-xl">
            Upload your dataset and let the NLP pipeline discover communication patterns, detect tone, and
            generate professional email templates.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <motion.a
              href="#actions"
              className="premium-button group"
              whileHover={{ y: -2, scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              transition={{ type: "spring", stiffness: 320, damping: 22 }}
            >
              Launch pipeline
              <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" aria-hidden="true" />
            </motion.a>
            <motion.a
              href="#templates"
              className="secondary-button"
              whileHover={{ y: -2 }}
              whileTap={{ scale: 0.98 }}
              transition={{ type: "spring", stiffness: 320, damping: 22 }}
            >
              Browse templates
            </motion.a>
          </div>
        </motion.div>

        <motion.div
          className="mx-auto mt-14 grid max-w-3xl grid-cols-1 gap-4 sm:grid-cols-3"
          initial={{ opacity: 0, y: 28 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        >
          {stats.map((item) => (
            <motion.div
              key={item.label}
              className="glass-card group relative overflow-hidden px-5 py-4 text-left"
              whileHover={{ y: -3 }}
              transition={{ type: "spring", stiffness: 240, damping: 22 }}
            >
              <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.06] text-cyan-200">
                <item.icon className="h-4 w-4" aria-hidden="true" />
              </div>
              <p className="text-2xl font-semibold tracking-tight text-white">{item.value}</p>
              <p className="mt-1 text-sm text-slate-400">{item.label}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
