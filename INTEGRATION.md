# Backend Integration Guide

This document is the contract between the email-template-generation backend
and any frontend / external client (e.g., the React Vite UI built
by Codex).

---

## 1. Project layout

```
email-template-generation/
├── backend/                 # FastAPI + ML pipeline
│   ├── main.py              # uvicorn entrypoint (backend.main:app)
│   ├── config.py            # env-driven settings (pydantic-settings)
│   ├── schemas.py           # Pydantic request/response models
│   ├── logging_config.py
│   ├── api/
│   │   ├── routes.py        # all HTTP endpoints
│   │   └── dependencies.py
│   ├── core/
│   │   ├── data_loader.py   # CSV loading + sample data generator
│   │   ├── preprocessing.py # signature/quote stripping, feature extraction
│   │   ├── embeddings.py    # SentenceTransformer wrapper + disk cache
│   │   ├── fine_tuning.py   # MultipleNegativesRankingLoss training
│   │   ├── clustering.py    # KMeans / DBSCAN / Agglomerative
│   │   ├── sentiment.py     # rule-based + optional transformer backend
│   │   ├── template_generator.py
│   │   ├── evaluation.py
│   │   └── pipeline.py      # end-to-end orchestrator + state singleton
│   └── utils/
├── frontend/
│   ├── package.json         # React + Vite frontend
│   ├── src/api/client.ts    # typed HTTP client used by React
│   ├── src/components/      # dashboard UI components
│   ├── api_client.py        # legacy Streamlit HTTP client
│   └── streamlit_app.py     # legacy Streamlit UI
├── data/
│   ├── raw/                 # uploaded CSVs land here
│   ├── processed/           # cleaned emails + embedding cache
│   └── sample_emails.csv    # 1100-row synthetic dataset
├── models/
│   └── fine_tuned_sentence_transformer/
├── outputs/
│   ├── templates.csv
│   ├── templates.json
│   └── templates.md
├── app.py                   # legacy streamlit run app.py
├── cli.py                   # command-line interface
└── tests/                   # pytest suite with mocked heavy ML calls
```

---

## 2. Local setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env           # tweak as needed
uvicorn backend.main:app --reload
```

The first call to `/api/run-pipeline` will:

1. Use `data/sample_emails.csv` (or the most recently uploaded CSV).
2. Download `sentence-transformers/all-MiniLM-L6-v2` (~90 MB) on first run.
3. Cache embeddings to `data/processed/embeddings.npy`.
4. Write templates to `outputs/templates.{csv,json,md}`.

### Skip the model download for tests

The pytest fixture `deterministic_embedder` patches `EmbeddingModel.encode`
with a hashed-bag-of-words encoder, so the suite runs in <3 s with no
network access.

---

## 3. HTTP API

All endpoints accept and return JSON unless noted. Schemas live in
[`backend/schemas.py`](backend/schemas.py).

| Method | Path                          | Purpose                                                |
| ------ | ----------------------------- | ------------------------------------------------------ |
| GET    | `/health`                     | Liveness check + summary of loaded artifacts           |
| POST   | `/api/upload`                 | Upload a CSV (multipart/form-data, field name `file`)  |
| POST   | `/api/run-pipeline`           | Run end-to-end pipeline                                |
| POST   | `/api/fine-tune`              | Fine-tune SentenceTransformer (supervised or pseudo)   |
| GET    | `/api/templates`              | List all generated templates                           |
| GET    | `/api/templates/{template_id}`| Fetch one template                                     |
| GET    | `/api/evaluation`             | Latest pipeline metrics                                |
| GET    | `/api/outputs/{format}`       | Download generated CSV, JSON, or Markdown templates    |
| POST   | `/api/generate-template`      | Match a raw email to the closest template              |

### Typical client flow

1. `POST /api/upload` (multipart) → server stores the file under `data/raw/`.
2. `POST /api/run-pipeline` `{ "clustering_method": "kmeans" }` → triggers
   the full pipeline. Response includes counts, evaluation metrics, and
   absolute paths to the persisted CSV/JSON/MD outputs.
3. `GET /api/templates` to render the gallery.
4. `GET /api/evaluation` to display the metrics dashboard.
5. `POST /api/generate-template` `{ "subject": "...", "body": "..." }` to
   suggest the closest template for a freshly typed email.

### Required CSV schema

Required columns: `email_id`, `subject`, `body`. Optional: `category`,
`sentiment`, `tone`, `sender`, `recipient`, `created_at`.

Extra columns are preserved. If `category` is absent, the fine-tuner
generates pseudo-labels via baseline KMeans (weak supervision).

### Status codes

- `400` — bad CSV, malformed payload, no labels available for fine-tuning.
- `404` — unknown `template_id`, missing CSV path.
- `409` — clients calling template/evaluation endpoints before the
  pipeline has been run.
- `500` — internal failure (logged with traceback).

---

## 4. Configuration knobs (`.env`)

| Key                              | Default                                          | Notes |
| -------------------------------- | ------------------------------------------------ | ----- |
| `EMBEDDING_MODEL_NAME`           | `sentence-transformers/all-MiniLM-L6-v2`         | any HF SBERT model id |
| `USE_FINE_TUNED`                 | `false`                                          | auto-loads from `FINE_TUNED_MODEL_DIR` if available |
| `EMBED_BATCH_SIZE`               | `64`                                             | |
| `CLUSTERING_METHOD`              | `kmeans`                                         | one of `kmeans`, `dbscan`, `agglomerative` |
| `N_CLUSTERS`                     | _heuristic_                                      | `round(sqrt(n/2))`, clamped 4–20 |
| `MAX_TEMPLATES`                  | `50`                                             | hard cap after dedup |
| `DUPLICATE_SIMILARITY_THRESHOLD` | `0.92`                                           | cosine threshold for collapsing near-duplicate templates |
| `SENTIMENT_BACKEND`              | `rule_based`                                     | `transformer` opts into HF pipeline |

---

## 5. Model lifecycle

- **Baseline embeddings** live in `data/processed/embeddings.npy` plus a
  `.meta` sidecar storing the corpus signature, so cache invalidation is
  automatic when the corpus or model changes.
- **Fine-tuned model** is saved to
  `models/fine_tuned_sentence_transformer/`. Set `USE_FINE_TUNED=true`
  (or pass `use_fine_tuned: true` in the pipeline payload) to load it.
- **Outputs** are overwritten on each run. Persist downstream if you
  need history.

---

## 6. Frontend integration tips (for Codex)

- The backend emits CORS `*` to keep dev simple — tighten in production.
- Endpoints are synchronous; long pipelines (>30 s on a fresh model
  download) should be wrapped in a UI loading state. There is no async
  job queue intentionally — keep the surface simple.
- All file paths in responses are absolute on the server filesystem.
  For browser display, use `templates.json` payload directly via the
  `/api/templates` endpoint instead of trying to fetch the file.
- The pipeline state is in-memory: a server restart wipes it. Re-run
  `/api/run-pipeline` to repopulate.

---

## 7. Testing

```bash
pytest                # fully mocked where ML would otherwise be expensive
pytest -k api         # just the HTTP integration tests
pytest -k clustering  # just the ML clustering tests
```

The suite is deliberately hermetic — it does not download models, hit
the network, or rely on the sample CSV being present.
