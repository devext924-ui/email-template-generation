"""Streamlit interface for the FastAPI email template backend."""

from __future__ import annotations

import html
import json
from typing import Any

import pandas as pd
import streamlit as st

from frontend.api_client import (
    ApiClientError,
    BackendUnavailableError,
    EmailTemplateApiClient,
    configured_backend_url,
)


CLUSTERING_METHODS = ["kmeans", "agglomerative", "dbscan"]
DOWNLOAD_FORMATS = {
    "csv": ("Download CSV", "text/csv"),
    "json": ("Download JSON", "application/json"),
    "markdown": ("Download Markdown", "text/markdown"),
}


def main() -> None:
    st.set_page_config(
        page_title="Email Template Generation",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _inject_css()
    _init_state()

    backend_url = _render_sidebar()
    client = EmailTemplateApiClient(backend_url)
    backend_ready = _render_backend_status(client)

    _render_header()
    run_tab, templates_tab, match_tab, downloads_tab = st.tabs(
        ["Pipeline", "Template Browser", "Raw Email Match", "Downloads"]
    )

    with run_tab:
        _render_pipeline_tab(client, backend_ready)
    with templates_tab:
        _render_templates_tab(client, backend_ready)
    with match_tab:
        _render_match_tab(client, backend_ready)
    with downloads_tab:
        _render_downloads_tab(client, backend_ready)


def _init_state() -> None:
    defaults = {
        "uploaded_csv_path": None,
        "pipeline_result": None,
        "fine_tune_result": None,
        "templates": [],
        "evaluation": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _render_sidebar() -> str:
    with st.sidebar:
        st.markdown("### Backend")
        backend_url = st.text_input(
            "FastAPI URL",
            value=st.session_state.get("backend_url", configured_backend_url()),
            help="Set EMAIL_TEMPLATE_BACKEND_URL to change the default.",
        ).rstrip("/")
        st.session_state["backend_url"] = backend_url

        st.markdown("### Quick Start")
        st.caption("1. Start FastAPI.")
        st.code("uvicorn backend.main:app --reload", language="bash")
        st.caption("2. Upload a CSV or use the bundled sample dataset.")
        st.caption("3. Run the pipeline, browse templates, and export outputs.")
        return backend_url


def _render_backend_status(client: EmailTemplateApiClient) -> bool:
    try:
        health = client.health()
    except BackendUnavailableError as exc:
        st.warning(str(exc))
        return False
    except ApiClientError as exc:
        st.error(f"Backend check failed: {exc}")
        return False

    st.sidebar.success(
        f"{health.get('app_name', 'Backend')} is online "
        f"({health.get('n_templates', 0)} templates loaded)."
    )
    return True


def _render_header() -> None:
    st.markdown(
        """
        <section class="hero">
            <div>
                <p class="eyebrow">NLP email operations workbench</p>
                <h1>Email Template Generation</h1>
                <p class="hero-copy">
                    Upload raw email datasets, cluster repeated intents with Sentence
                    Transformer embeddings, and turn noisy communication into reusable,
                    professional templates.
                </p>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_pipeline_tab(client: EmailTemplateApiClient, backend_ready: bool) -> None:
    left, right = st.columns([1.15, 0.85], gap="large")

    with left:
        st.subheader("Dataset")
        uploaded = st.file_uploader(
            "Upload CSV",
            type=["csv"],
            help="Required columns: email_id, subject, body. Optional columns improve labels.",
            disabled=not backend_ready,
        )
        upload_col, sample_col = st.columns([0.45, 0.55])
        with upload_col:
            if st.button("Upload CSV", disabled=not backend_ready or uploaded is None):
                assert uploaded is not None
                with st.spinner("Uploading and validating CSV..."):
                    _handle_upload(client, uploaded.name, uploaded.getvalue())

        with sample_col:
            st.info(
                "No upload needed for a demo run. If CSV path is empty, the backend uses "
                "`data/sample_emails.csv` or the most recent upload."
            )

        csv_path = st.text_input(
            "CSV path passed to pipeline",
            value=st.session_state.get("uploaded_csv_path") or "",
            placeholder="Leave blank to use backend sample data",
            disabled=not backend_ready,
        )

        st.subheader("Pipeline Controls")
        method = st.selectbox("Clustering method", CLUSTERING_METHODS, disabled=not backend_ready)
        use_fine_tuned = st.toggle("Use fine-tuned Sentence Transformer", value=False)
        auto_clusters = st.toggle("Let backend choose cluster count", value=True)
        n_clusters = None
        if not auto_clusters:
            n_clusters = st.number_input(
                "Number of clusters",
                min_value=2,
                max_value=100,
                value=10,
                step=1,
                disabled=not backend_ready,
            )

        if st.button("Run Pipeline", type="primary", disabled=not backend_ready):
            with st.spinner("Running preprocessing, embeddings, clustering, and template generation..."):
                _handle_pipeline_run(
                    client,
                    csv_path=csv_path.strip() or None,
                    use_fine_tuned=use_fine_tuned,
                    n_clusters=int(n_clusters) if n_clusters else None,
                    clustering_method=method,
                )

    with right:
        st.subheader("Metrics Dashboard")
        _render_metrics(st.session_state.get("evaluation"))
        st.divider()
        st.subheader("Fine-Tuning")
        st.caption(
            "Fine-tuning can take a while on CPU. It uses the backend's labeled or "
            "weakly supervised pair generation."
        )
        epochs = st.number_input("Epochs", min_value=1, max_value=10, value=1, step=1)
        batch_size = st.number_input("Batch size", min_value=2, max_value=128, value=16, step=2)
        use_pseudo = st.toggle("Use pseudo-labels when labels are sparse", value=True)
        if st.button("Fine-Tune Model", disabled=not backend_ready):
            with st.spinner("Fine-tuning Sentence Transformer embeddings..."):
                _handle_fine_tune(
                    client,
                    csv_path=csv_path.strip() or None,
                    epochs=int(epochs),
                    batch_size=int(batch_size),
                    use_pseudo_labels=use_pseudo,
                )
        _render_fine_tune_summary(st.session_state.get("fine_tune_result"))


def _handle_upload(client: EmailTemplateApiClient, filename: str, content: bytes) -> None:
    try:
        result = client.upload_csv(filename, content)
    except ApiClientError as exc:
        st.error(f"Upload failed: {exc}")
        return
    st.session_state["uploaded_csv_path"] = result["saved_path"]
    st.success(f"Uploaded {result['filename']} with {result['rows']} rows.")


def _handle_pipeline_run(
    client: EmailTemplateApiClient,
    *,
    csv_path: str | None,
    use_fine_tuned: bool,
    n_clusters: int | None,
    clustering_method: str,
) -> None:
    try:
        result = client.run_pipeline(
            csv_path=csv_path,
            use_fine_tuned=use_fine_tuned,
            n_clusters=n_clusters,
            clustering_method=clustering_method,
        )
        templates = client.list_templates()["templates"]
        evaluation = client.get_evaluation()
    except ApiClientError as exc:
        st.error(f"Pipeline failed: {exc}")
        return

    st.session_state["pipeline_result"] = result
    st.session_state["templates"] = templates
    st.session_state["evaluation"] = evaluation
    st.success(
        f"Pipeline completed: {result['n_emails']} emails, "
        f"{result['n_clusters']} clusters, {result['n_templates']} templates."
    )


def _handle_fine_tune(
    client: EmailTemplateApiClient,
    *,
    csv_path: str | None,
    epochs: int,
    batch_size: int,
    use_pseudo_labels: bool,
) -> None:
    try:
        result = client.fine_tune(
            csv_path=csv_path,
            epochs=epochs,
            batch_size=batch_size,
            use_pseudo_labels=use_pseudo_labels,
        )
    except ApiClientError as exc:
        st.error(f"Fine-tuning failed: {exc}")
        return

    st.session_state["fine_tune_result"] = result
    st.success(f"Fine-tuned model saved to {result['model_path']}.")


def _render_templates_tab(client: EmailTemplateApiClient, backend_ready: bool) -> None:
    header_col, refresh_col = st.columns([0.8, 0.2])
    with header_col:
        st.subheader("Template Browser")
    with refresh_col:
        if st.button("Refresh", disabled=not backend_ready):
            _refresh_templates(client)

    templates = st.session_state.get("templates") or []
    if not templates and backend_ready:
        _refresh_templates(client, quiet=True)
        templates = st.session_state.get("templates") or []

    if not templates:
        st.info("Run the pipeline first to populate the template browser.")
        return

    filtered = _filter_templates(templates)
    if not filtered:
        st.warning("No templates match the current filters.")
        return

    selected = st.selectbox(
        "Select a template",
        filtered,
        format_func=lambda item: _template_label(item),
    )
    _render_template_card(selected)

    with st.expander("Template table"):
        table = pd.DataFrame(filtered)
        if "body_template" in table.columns:
            table = table.drop(columns=["body_template"])
        st.dataframe(table, use_container_width=True, hide_index=True)


def _refresh_templates(client: EmailTemplateApiClient, *, quiet: bool = False) -> None:
    try:
        st.session_state["templates"] = client.list_templates()["templates"]
        st.session_state["evaluation"] = client.get_evaluation()
    except ApiClientError as exc:
        if not quiet:
            st.warning(f"Templates are not ready yet: {exc}")


def _filter_templates(templates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    categories = sorted({tpl.get("category") for tpl in templates if tpl.get("category")})
    tones = sorted({tpl.get("tone") for tpl in templates if tpl.get("tone")})
    c1, c2, c3 = st.columns([0.3, 0.3, 0.4])
    category = c1.selectbox("Category", ["All", *categories])
    tone = c2.selectbox("Tone", ["All", *tones])
    query = c3.text_input("Search subject/body/intent").strip().lower()

    filtered = []
    for tpl in templates:
        if category != "All" and tpl.get("category") != category:
            continue
        if tone != "All" and tpl.get("tone") != tone:
            continue
        haystack = " ".join(
            str(tpl.get(key, ""))
            for key in ("subject_template", "body_template", "intent", "category", "tone")
        ).lower()
        if query and query not in haystack:
            continue
        filtered.append(tpl)
    return filtered


def _render_template_card(template: dict[str, Any]) -> None:
    subject = html.escape(str(template.get("subject_template", "")))
    meta = " | ".join(
        item
        for item in [
            f"cluster {template.get('cluster_id')}",
            f"{template.get('cluster_size')} emails",
            str(template.get("category") or ""),
            str(template.get("tone") or ""),
            str(template.get("sentiment") or ""),
        ]
        if item
    )
    st.markdown(
        f"""
        <article class="template-card">
            <p class="eyebrow">{html.escape(meta)}</p>
            <h3>{subject}</h3>
        </article>
        """,
        unsafe_allow_html=True,
    )
    st.code(str(template.get("body_template", "")), language="markdown")
    placeholders = template.get("placeholders") or []
    if placeholders:
        st.caption("Placeholders: " + ", ".join(f"`{{{p}}}`" for p in placeholders))


def _render_match_tab(client: EmailTemplateApiClient, backend_ready: bool) -> None:
    st.subheader("Match a Raw Email to the Best Template")
    st.caption("This calls `/api/generate-template` and uses the backend's latest pipeline state.")

    subject = st.text_input("Subject", placeholder="Following up on the proposal")
    body = st.text_area(
        "Raw email body",
        height=220,
        placeholder=(
            "Hi Jordan,\n\nJust checking whether you had a chance to review the proposal. "
            "Happy to answer questions.\n\nThanks,\nTaylor"
        ),
    )
    top_k = st.slider("Number of matches", min_value=1, max_value=5, value=3)

    if st.button("Find Matching Template", type="primary", disabled=not backend_ready):
        if not body.strip():
            st.warning("Add an email body before matching.")
            return
        with st.spinner("Embedding the email and comparing it against generated templates..."):
            try:
                result = client.generate_template(subject=subject or None, body=body, top_k=top_k)
            except ApiClientError as exc:
                st.error(f"Could not match template: {exc}")
                return

        st.success(
            f"Detected tone: {result.get('detected_tone') or 'unknown'} | "
            f"sentiment: {result.get('detected_sentiment') or 'unknown'}"
        )
        for match in result.get("matches", []):
            similarity = match.get("similarity", 0)
            st.metric("Similarity", f"{similarity:.3f}")
            _render_template_card(match["template"])


def _render_downloads_tab(client: EmailTemplateApiClient, backend_ready: bool) -> None:
    st.subheader("Export Generated Templates")
    st.caption("Download buttons call the backend output endpoint, so they work from Streamlit cleanly.")

    result = st.session_state.get("pipeline_result")
    if result:
        st.info(
            "Latest output paths: "
            f"`{result.get('templates_csv')}`, `{result.get('templates_json')}`, "
            f"`{result.get('templates_md')}`"
        )

    cols = st.columns(3)
    for idx, (fmt, (label, mime)) in enumerate(DOWNLOAD_FORMATS.items()):
        with cols[idx]:
            if not backend_ready:
                st.button(label, disabled=True)
                continue
            try:
                download = client.download_output(fmt)
            except ApiClientError as exc:
                st.button(label, disabled=True)
                st.caption(f"Run the pipeline first. {exc}")
                continue
            st.download_button(
                label,
                data=download.content,
                file_name=download.filename,
                mime=mime,
                use_container_width=True,
            )


def _render_metrics(metrics: dict[str, Any] | None) -> None:
    if not metrics:
        st.info("Metrics appear here after a pipeline run.")
        return

    m1, m2, m3 = st.columns(3)
    m1.metric("Emails", _metric(metrics.get("n_emails")))
    m2.metric("Clusters", _metric(metrics.get("n_clusters")))
    m3.metric("Templates", _metric(metrics.get("n_templates")))

    m4, m5, m6 = st.columns(3)
    m4.metric("Silhouette", _metric(metrics.get("silhouette_score"), digits=3))
    m5.metric("Coverage", _metric(metrics.get("template_coverage"), digits=1, percent=True))
    m6.metric(
        "Duplicate %",
        _metric(metrics.get("duplicate_template_percentage"), digits=1, percent=True),
    )

    with st.expander("All evaluation metrics"):
        st.json(metrics)


def _render_fine_tune_summary(result: dict[str, Any] | None) -> None:
    if not result:
        return
    st.markdown("#### Latest Fine-Tune")
    st.json(
        {
            "model_path": result.get("model_path"),
            "epochs": result.get("epochs"),
            "pairs": result.get("n_pairs"),
            "improvement": result.get("improvement"),
            "duration_seconds": result.get("duration_seconds"),
        }
    )


def _template_label(template: dict[str, Any]) -> str:
    category = template.get("category") or "uncategorized"
    subject = template.get("subject_template") or template.get("template_id")
    return f"{category} | {subject}"


def _metric(value: Any, *, digits: int = 0, percent: bool = False) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        display = value * 100 if percent else value
        return f"{display:.{digits}f}{'%' if percent else ''}"
    return str(value)


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #16211f;
            --muted: #5e6a64;
            --paper: #fffaf0;
            --mint: #d5eadf;
            --clay: #c7603c;
            --forest: #1d4f43;
        }
        .stApp {
            color: var(--ink);
            background:
                radial-gradient(circle at top left, rgba(213, 234, 223, 0.95), transparent 34rem),
                linear-gradient(135deg, #fffaf0 0%, #f4efe3 45%, #e7f0e8 100%);
            font-family: "Avenir Next", "Gill Sans", "Trebuchet MS", sans-serif;
        }
        .hero {
            border: 1px solid rgba(29, 79, 67, 0.18);
            border-radius: 28px;
            padding: 2rem;
            margin-bottom: 1rem;
            background:
                linear-gradient(135deg, rgba(255, 250, 240, 0.92), rgba(213, 234, 223, 0.76)),
                radial-gradient(circle at right, rgba(199, 96, 60, 0.16), transparent 18rem);
            box-shadow: 0 20px 50px rgba(29, 79, 67, 0.12);
        }
        .hero h1 {
            margin: 0;
            font-size: clamp(2.4rem, 6vw, 4.8rem);
            letter-spacing: -0.07em;
            line-height: 0.92;
            color: var(--forest);
        }
        .hero-copy {
            max-width: 780px;
            color: var(--muted);
            font-size: 1.08rem;
            line-height: 1.65;
        }
        .eyebrow {
            margin: 0 0 0.4rem;
            color: var(--clay);
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }
        .template-card {
            border: 1px solid rgba(29, 79, 67, 0.16);
            border-radius: 22px;
            padding: 1.1rem 1.25rem;
            background: rgba(255, 250, 240, 0.78);
            box-shadow: 0 12px 30px rgba(22, 33, 31, 0.08);
        }
        .template-card h3 {
            margin: 0;
            color: var(--forest);
            letter-spacing: -0.03em;
        }
        div[data-testid="stMetric"] {
            background: rgba(255, 250, 240, 0.72);
            border: 1px solid rgba(29, 79, 67, 0.12);
            border-radius: 18px;
            padding: 0.75rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
