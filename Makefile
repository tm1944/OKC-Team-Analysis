.PHONY: install run test lint db-up db-down db-logs migrate ingest-teams ingest-games ingest-players ingest-shots ingest-pbp ingest-all train-model index-knowledge

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

migrate:
	uv run python migrate.py

ingest-teams:
	uv run python scripts/ingest.py teams

ingest-games:
	uv run python scripts/ingest.py games

ingest-players:
	uv run python scripts/ingest.py players

ingest-shots:
	uv run python scripts/ingest.py shots

ingest-pbp:
	uv run python scripts/ingest.py play-by-play

ingest-all:
	uv run python scripts/ingest.py all

train-model:
	uv run python scripts/train_model.py

index-knowledge:
	uv run python scripts/index_knowledge.py
