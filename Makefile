.PHONY: install run test lint format

install:
	uv sync

run:
	PYTHONPATH=. uv run uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload

test:
	PYTHONPATH=. uv run pytest

lint:
	PYTHONPATH=. uv run ruff check .

format:
	PYTHONPATH=. uv run ruff format .
