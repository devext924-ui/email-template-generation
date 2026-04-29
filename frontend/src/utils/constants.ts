export const CLUSTERING_METHODS = ["kmeans", "agglomerative", "dbscan"] as const;

export const SAMPLE_EMAIL = `Hi Jordan,

Just checking whether you had a chance to review the migration plan I sent over last week. Happy to answer questions or jump on a quick call if that is easier.

Thanks,
Taylor`;

export const DOWNLOADS = [
  { format: "csv", label: "CSV", filename: "templates.csv" },
  { format: "json", label: "JSON", filename: "templates.json" },
  { format: "markdown", label: "Markdown", filename: "templates.md" },
] as const;

export const fadeUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] },
};
