import { motion } from "motion/react";
import { ArrowRight, Layers3, WandSparkles } from "lucide-react";
import { fadeUp } from "../utils/constants";

interface HeroSectionProps {
  templateCount: number;
  emailCount: number;
}

export function HeroSection({ templateCount, emailCount }: HeroSectionProps) {
  return (
    <section className="relative overflow-hidden px-4 pb-12 pt-14 sm:px-6 lg:px-8 lg:pb-16 lg:pt-20">
      <motion.div
        className="pointer-events-none absolute left-1/2 top-8 h-80 w-80 -translate-x-1/2 rounded-full bg-cyan-500/25 blur-[110px]"
        animate={{ scale: [1, 1.16, 1], opacity: [0.5, 0.85, 0.5] }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="pointer-events-none absolute right-10 top-28 h-72 w-72 rounded-full bg-violet-500/20 blur-[110px]"
        animate={{ x: [0, -28, 0], y: [0, 22, 0] }}
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
      />

      <div className="relative mx-auto max-w-7xl">
        <motion.div
          className="mx-auto max-w-5xl text-center"
          initial={fadeUp.initial}
          animate={fadeUp.animate}
          transition={fadeUp.transition}
        >
          <div className="mx-auto mb-7 inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-4 py-2 text-sm font-medium text-cyan-100 shadow-glow">
            <WandSparkles className="h-4 w-4" aria-hidden="true" />
            FastAPI powered NLP template intelligence
          </div>
          <h2 className="text-balance bg-gradient-to-b from-white via-slate-100 to-slate-500 bg-clip-text text-5xl font-semibold tracking-[-0.06em] text-transparent sm:text-6xl lg:text-7xl">
            Transform raw emails into reusable templates.
          </h2>
          <p className="mx-auto mt-7 max-w-3xl text-balance text-lg leading-8 text-slate-300 sm:text-xl">
            Upload your dataset and let the NLP pipeline discover communication patterns,
            detect tone, and generate professional email templates.
          </p>
          <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <a href="#actions" className="premium-button group">
              Launch pipeline
              <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" aria-hidden="true" />
            </a>
            <a href="#templates" className="secondary-button">
              Browse templates
            </a>
          </div>
        </motion.div>

        <motion.div
          className="mx-auto mt-12 grid max-w-3xl grid-cols-1 gap-4 sm:grid-cols-3"
          initial={{ opacity: 0, y: 28 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.55 }}
        >
          {[
            { label: "Emails loaded", value: emailCount || "Ready" },
            { label: "Templates generated", value: templateCount || "Awaiting run" },
            { label: "Output formats", value: "CSV / JSON / MD" },
          ].map((item) => (
            <div key={item.label} className="glass-card px-5 py-4 text-left">
              <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-2xl bg-white/[0.08] text-cyan-200">
                <Layers3 className="h-4 w-4" aria-hidden="true" />
              </div>
              <p className="text-2xl font-semibold tracking-tight text-white">{item.value}</p>
              <p className="mt-1 text-sm text-slate-400">{item.label}</p>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
