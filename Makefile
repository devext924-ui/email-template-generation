.PHONY: install frontend-install backend frontend frontend-build streamlit-legacy cli-sample cli-run test clean

install:
	python -m pip install -r requirements.txt
	cd frontend && npm install

frontend-install:
	cd frontend && npm install

backend:
	uvicorn backend.main:app --reload

frontend:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

streamlit-legacy:
	streamlit run app.py

cli-sample:
	python cli.py load-sample

cli-run:
	python cli.py run --input data/sample_emails.csv

test:
	pytest

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .mypy_cache *.egg-info frontend/dist frontend/*.tsbuildinfo frontend/vite.config.js frontend/vite.config.d.ts
