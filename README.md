# Basketball decision support API

This project uses the 2024-25 Oklahoma City Thunder regular season to practice a full data-and-AI workflow. It loads NBA data into PostgreSQL, trains a small PyTorch shot model, retrieves local basketball notes with pgvector, and exposes the result through FastAPI.

It is a learning project, not a replacement for a coaching staff. The model estimates shot-make probability. The RAG notes give the answer context. The database supplies the numbers.

## What the API returns

`POST /analyze-player` accepts a player name, a question, optional filters, and an optional shot scenario. It returns shooting statistics, a model probability when the scenario is complete, retrieved evidence, generated analysis, and known limitations.

Version one supports players only. It has OKC shots and play-by-play from OKC games. It does not have possession-level defensive coverage labels, so questions about drop coverage return that limitation rather than pretend the data proves something it does not.

## Data flow

```text
NBA Stats API
  -> cached JSON in data/raw/nba/
  -> PostgreSQL 16 and pgvector
  -> SQL features and PyTorch model
  -> FastAPI
  -> exact vector retrieval and optional OpenAI response
```

## Requirements

- Python 3.14
- [uv](https://docs.astral.sh/uv/)
- Docker Desktop
- An OpenAI API key for live knowledge indexing and generated analysis

## Start the local database

```bash
cp .env.example .env
uv sync --dev
make db-up
make migrate
```

The database uses port `5433`. That avoids connecting to a Homebrew PostgreSQL server that may already occupy port `5432`.

## Load the OKC season

NBA responses are cached in ignored `data/raw/nba/`. Run the loaders in this order because facts need their parent rows first.

```bash
make ingest-teams
make ingest-games
make ingest-players
make ingest-shots
make ingest-pbp
```

Play-by-play makes a request for each OKC game. Test that source with one game before loading all 82:

```bash
uv run python scripts/ingest.py play-by-play --max-games 1
```

`make ingest-all` runs the complete sequence. Add `--refresh` to a source command when you intentionally want a new raw NBA response.

## Train the shot model

```bash
make train-model
```

Training keeps whole games in time order. It uses the first 70% of games for training, the next 15% for validation, and the last 15% for the test set. Player and zone vocabularies plus numeric scaling are fitted on training data only.

The model has an 8-value player embedding, a 3-value zone embedding, normalized distance, period, clock, home or away, a 16-unit ReLU layer, and one output logit. It saves model weights and JSON metadata under ignored `artifacts/`.

## Index the knowledge base

The starter notes live in `documents/`. They include a Shai scouting note, an OKC profile, four game summaries, and glossary entries. Each file records its source in frontmatter.

Set `OPENAI_API_KEY` in `.env`, then run:

```bash
make index-knowledge
```

The indexer chunks Markdown by paragraph, embeds it with `text-embedding-3-small`, and stores 1,536-value vectors in pgvector. The corpus is small enough that exact cosine search is the right tradeoff.

## Run and call the API

```bash
make run
```

Open `http://127.0.0.1:8000/docs` for interactive docs.

```bash
curl -X POST http://127.0.0.1:8000/analyze-player \
  -H 'content-type: application/json' \
  -d '{
    "player": "Shai Gilgeous-Alexander",
    "question": "How effective is he near the rim recently?",
    "filters": {"last_n_games": 10},
    "shot_context": {
      "shot_distance_ft": 3,
      "shot_zone": "Restricted Area",
      "quarter": 4,
      "seconds_remaining": 90,
      "is_home": true
    }
  }'
```

Omit `shot_context` if you only want statistics and evidence. The API then returns `model_prediction.status` as `not_requested`.

`GET /health/live` checks FastAPI. `GET /health/ready` also checks PostgreSQL, pgvector, migrations, and model artifacts. It does not call OpenAI.

## Docker

```bash
docker compose up --build
```

The API container connects to the Compose database and mounts local `artifacts/` read-only. Train the model on the host first if you want predictions in the container.

## Tests

```bash
make test
make lint
```

The tests use fake embedding and generation services. They do not spend OpenAI credits. `.agents/` holds local learning notes and implementation decisions. Git ignores it, along with `.env`, raw responses, local database files, and model artifacts.
