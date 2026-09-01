# Basketball decision support API

This project will analyze 2024-25 Oklahoma City Thunder players using PostgreSQL statistics, a small PyTorch shot model, and a pgvector knowledge base.

## Current state

The project setup and live health endpoint are ready. Ticket 1 begins with the relational schema. The detailed learning tasks live locally in `.agents/`, which Git ignores on purpose.

## Setup

```bash
cp .env.example .env
uv sync --dev
docker compose up -d postgres
uv run uvicorn basketball_api.app:app --reload
```

Check `http://127.0.0.1:8000/health/live` or the generated API docs at `http://127.0.0.1:8000/docs`.

## Tests

```bash
uv run pytest
uv run ruff check .
uv run mypy src
```

Live NBA and OpenAI tests will use the `live` pytest marker and will remain opt-in.

