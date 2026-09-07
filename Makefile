.PHONY: install run check evaluate docs

install:
	python3.12 -m venv .venv
	.venv/bin/pip install -e ".[dev]"

run:
	.venv/bin/streamlit run app.py

check:
	.venv/bin/ruff check .
	.venv/bin/mypy deliverybrief
	.venv/bin/pytest
	.venv/bin/python scripts/check_secrets.py

evaluate:
	.venv/bin/python -m deliverybrief.evaluation --dataset evaluation/cases --model demo --output evaluation/results/demo-latest.json

docs:
	.venv/bin/python scripts/build_submission_documents.py
