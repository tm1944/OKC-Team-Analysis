#!/usr/bin/env python
"""Ingest 2024-25 NBA source data into the local PostgreSQL database."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import psycopg

from basketball_api.config import get_settings
from basketball_api.season_ingestion import (
    ingest_all,
    ingest_games,
    ingest_play_by_play,
    ingest_players,
    ingest_shots,
    ingest_teams,
)


def parse_args() -> argparse.Namespace:
    settings = get_settings()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source",
        choices=("teams", "games", "players", "shots", "play-by-play", "all"),
    )
    parser.add_argument("--season", default=settings.nba_season)
    parser.add_argument("--team-id", type=int, default=settings.nba_team_id)
    parser.add_argument("--cache-dir", type=Path, default=Path("data/raw/nba"))
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--max-games", type=int)
    parser.add_argument("--sleep-seconds", type=float, default=0.6)
    return parser.parse_args()


def run_source(conn: Any, args: argparse.Namespace) -> dict[str, int]:
    common = {
        "cache_dir": args.cache_dir,
        "season": args.season,
        "team_id": args.team_id,
        "refresh": args.refresh,
    }
    if args.source == "teams":
        return ingest_teams(conn, cache_dir=args.cache_dir, refresh=args.refresh)
    if args.source == "games":
        return ingest_games(conn, **common)
    if args.source == "players":
        return ingest_players(conn, **common)
    if args.source == "shots":
        return ingest_shots(conn, **common)
    if args.source == "play-by-play":
        return ingest_play_by_play(
            conn,
            **common,
            max_games=args.max_games,
            sleep_seconds=args.sleep_seconds,
        )
    return ingest_all(
        conn,
        **common,
        max_games=args.max_games,
        sleep_seconds=args.sleep_seconds,
    )


def main() -> None:
    args = parse_args()
    settings = get_settings()
    with psycopg.connect(settings.database_url) as conn:
        counts = run_source(conn, args)
    print(f"Completed {args.source}: {counts}")


if __name__ == "__main__":
    main()

