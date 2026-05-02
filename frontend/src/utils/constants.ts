export const CLUSTERING_METHODS = ["kmeans", "agglomerative", "dbscan"] as const;

export const SAMPLE_EMAIL = `Hi Jordan,

Just checking whether you had a chance to review the migration plan I sent over last week. Happy to answer questions or jump on a quick call if that is easier.

Thanks,
Taylor`;

export const DOWNLOADS = [
  {
    format: "csv",
    label: "CSV",
    filename: "templates.csv",
    description: "Spreadsheet-friendly export with every template field.",
  },
  {
    format: "json",
    label: "JSON",
    filename: "templates.json",
    description: "Structured payload for APIs, ETL, and downstream services.",
  },
  {
    format: "markdown",
    label: "Markdown",
    filename: "templates.md",
    description: "Human-readable doc for review, notes, and handoffs.",
  },
] as const;

const easeOutExpo = [0.22, 1, 0.36, 1] as const;

export const fadeUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.55, ease: easeOutExpo },
};

export const fadeUpSm = {
  initial: { opacity: 0, y: 14 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4, ease: easeOutExpo },
};

export const staggerContainer = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: 0.07,
      delayChildren: 0.04,
    },
  },
};

export const staggerItem = {
  initial: { opacity: 0, y: 18 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.45, ease: easeOutExpo },
  },
};
