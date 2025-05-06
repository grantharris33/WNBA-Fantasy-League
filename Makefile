.PHONY: dev test lint format

dev:
	poetry run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

test:
	poetry run pytest

lint:
	poetry run ruff . && poetry run isort --check-only . && poetry run black --check .

format:
	poetry run ruff --fix . && poetry run isort . && poetry run black .