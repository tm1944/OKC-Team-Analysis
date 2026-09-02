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

## Ticket 1: ingest the OKC season

Run migrations once the database container is healthy:

```bash
make migrate
```

The ingestion command caches NBA responses in ignored `data/raw/nba/` and safely
upserts into PostgreSQL. Run sources in this order because games and players must
exist before shots and play-by-play can reference them:

```bash
make ingest-teams
make ingest-games
make ingest-players
make ingest-shots
make ingest-pbp
```

`make ingest-pbp` fetches all 82 games and is the longest step. Start with one
game while checking your setup:

```bash
uv run python scripts/ingest.py play-by-play --max-games 1
```

To run every source in sequence, use `make ingest-all`. Add `--refresh` to the
underlying command only when you deliberately want to replace cached NBA responses.

## Ticket 2: train the shot model

After games, players, and shots are loaded, train the small local PyTorch model:

```bash
make train-model
```

This writes ignored state-dictionary and JSON metadata artifacts under `artifacts/`.
The training command preserves time order: it fits vocabularies and numeric scaling on
the first 70% of games, validates on the next 15%, and reports final metrics on the
last 15%.

## Tickets 3 and 4: knowledge and API

Committed Markdown evidence lives in `documents/`. Set `OPENAI_API_KEY` in ignored `.env`,
then run `make migrate` and `make index-knowledge` to create live embeddings. Start the API
with `make run`; `/health/live` checks the process and `/health/ready` also checks PostgreSQL,
pgvector, migrations, and model artifacts without calling OpenAI.

```bash
curl -X POST http://127.0.0.1:8000/analyze-player \
  -H 'content-type: application/json' \
  -d '{"player":"Shai Gilgeous-Alexander","question":"How effective is he near the rim recently?","shot_context":{"shot_distance_ft":3,"shot_zone":"Restricted Area","quarter":4,"seconds_remaining":90,"is_home":true}}'
```

## Tests

```bash
uv run pytest
uv run ruff check .
uv run mypy src
```

Live NBA and OpenAI tests will use the `live` pytest marker and will remain opt-in.
