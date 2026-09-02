#!/usr/bin/env python
"""Train and save the version-one shot-make model from PostgreSQL data."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

from basketball_api.artifacts import save_artifact
from basketball_api.config import get_settings
from basketball_api.features import SHOT_FEATURES_FOR_SEASON_SQL
from basketball_api.preprocessing import ShotPreprocessor
from basketball_api.splits import chronological_game_split
from basketball_api.training import evaluate_model, train_model


def parse_args() -> argparse.Namespace:
    settings = get_settings()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", default=settings.nba_season)
    parser.add_argument("--state-path", type=Path, default=settings.model_artifact_path)
    parser.add_argument("--metadata-path", type=Path, default=settings.model_metadata_path)
    return parser.parse_args()


def load_rows(database_url: str, season: str) -> list[dict[str, Any]]:
    with psycopg.connect(database_url, row_factory=dict_row) as conn:
        return list(conn.execute(SHOT_FEATURES_FOR_SEASON_SQL, (season,)).fetchall())


def main() -> None:
    args = parse_args()
    settings = get_settings()
    rows = load_rows(settings.database_url, args.season)
    training_rows, validation_rows, test_rows = chronological_game_split(rows)
    preprocessor = ShotPreprocessor.fit(training_rows)
    result = train_model(training_rows, validation_rows, preprocessor)
    metrics = evaluate_model(result.model, test_rows, preprocessor)
    save_artifact(
        result.model,
        preprocessor,
        metrics,
        state_path=args.state_path,
        metadata_path=args.metadata_path,
        data_range={
            "start": str(training_rows[0]["game_date"]),
            "end": str(test_rows[-1]["game_date"]),
        },
    )
    print(f"Saved {args.state_path} and {args.metadata_path}")
    print(f"Test metrics: {metrics}")


if __name__ == "__main__":
    main()
