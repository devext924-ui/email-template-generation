"""Documentation and project packaging smoke tests."""

from __future__ import annotations


def test_readme_contains_required_run_commands(project_root):
    readme = (project_root / "README.md").read_text(encoding="utf-8")

    required = [
        "uvicorn backend.main:app --reload",
        "cd frontend",
        "npm run dev",
        "python cli.py run --input data/sample_emails.csv",
        "python cli.py fine-tune --input data/sample_emails.csv",
        "python cli.py templates --format markdown",
    ]
    for command in required:
        assert command in readme


def test_packaging_files_exist(project_root):
    for relative_path in [
        "app.py",
        "cli.py",
        "frontend/package.json",
        "frontend/src/App.tsx",
        "frontend/src/api/client.ts",
        "frontend/streamlit_app.py",
        "frontend/api_client.py",
        ".env.example",
        ".gitignore",
        "Makefile",
        "resume_summary.md",
    ]:
        assert (project_root / relative_path).exists()
