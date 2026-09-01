.PHONY: install run test lint db-up db-down db-logs

install:
	uv sync --dev

run:
	uv run uvicorn basketball_api.app:app --reload

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run mypy src

db-up:
	docker compose up -d postgres

db-down:
	docker compose down

db-logs:
	docker compose logs -f postgres

