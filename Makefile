.PHONY: dev test lint format

dev:
	poetry run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

test:
	poetry run pytest

lint:
	poetry run ruff . && poetry run black --check . && poetry run isort --check-only .

format:
	poetry run ruff --fix . && poetry run black . && poetry run isort . 