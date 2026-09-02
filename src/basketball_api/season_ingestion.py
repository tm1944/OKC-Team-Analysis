"""Insert cached NBA source records into the local basketball database."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from basketball_api.ingestion import normalize_payload
from basketball_api.insert import insert_normalized_payload
from basketball_api.nba_sources import (
    league_game_records,
    play_by_play_records,
    player_records_from_shots,
    roster_records,
    shot_records,
    team_records,
)


def _insert(conn: Any, payload: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    counts = insert_normalized_payload(conn, normalize_payload(payload))
    conn.commit()
    return counts


def ingest_teams(conn: Any, *, cache_dir: Path, refresh: bool) -> dict[str, int]:
    return _insert(conn, {"teams": team_records(cache_dir, refresh=refresh)})


def ingest_games(
    conn: Any,
    *,
    cache_dir: Path,
    season: str,
    team_id: int,
    refresh: bool,
) -> dict[str, int]:
    games, team_games = league_game_records(
        cache_dir,
        season=season,
        team_id=team_id,
        refresh=refresh,
    )
    return _insert(conn, {"games": games, "team_games": team_games})


def ingest_players(
    conn: Any,
    *,
    cache_dir: Path,
    season: str,
    team_id: int,
    refresh: bool,
) -> dict[str, int]:
    return _insert(
        conn,
        {"players": roster_records(cache_dir, season=season, team_id=team_id, refresh=refresh)},
    )


def ingest_shots(
    conn: Any,
    *,
    cache_dir: Path,
    season: str,
    team_id: int,
    refresh: bool,
) -> dict[str, int]:
    shots = shot_records(cache_dir, season=season, team_id=team_id, refresh=refresh)
    return _insert(
        conn,
        {"players": player_records_from_shots(shots), "shots": shots},
    )


def ingest_play_by_play(
    conn: Any,
    *,
    cache_dir: Path,
    season: str,
    team_id: int,
    refresh: bool,
    max_games: int | None,
    sleep_seconds: float,
) -> dict[str, int]:
    games, _ = league_game_records(
        cache_dir,
        season=season,
        team_id=team_id,
        refresh=refresh,
    )
    game_ids = [game["id"] for game in games]
    if max_games is not None:
        game_ids = game_ids[:max_games]
    players, actions = play_by_play_records(
        cache_dir,
        season=season,
        game_ids=game_ids,
        refresh=refresh,
        sleep_seconds=sleep_seconds,
    )
    return _insert(conn, {"players": players, "play_by_play": actions})


def ingest_all(
    conn: Any,
    *,
    cache_dir: Path,
    season: str,
    team_id: int,
    refresh: bool,
    max_games: int | None,
    sleep_seconds: float,
) -> dict[str, int]:
    totals: dict[str, int] = {}
    for ingest in (
        lambda: ingest_teams(conn, cache_dir=cache_dir, refresh=refresh),
        lambda: ingest_games(
            conn,
            cache_dir=cache_dir,
            season=season,
            team_id=team_id,
            refresh=refresh,
        ),
        lambda: ingest_players(
            conn,
            cache_dir=cache_dir,
            season=season,
            team_id=team_id,
            refresh=refresh,
        ),
        lambda: ingest_shots(
            conn,
            cache_dir=cache_dir,
            season=season,
            team_id=team_id,
            refresh=refresh,
        ),
        lambda: ingest_play_by_play(
            conn,
            cache_dir=cache_dir,
            season=season,
            team_id=team_id,
            refresh=refresh,
            max_games=max_games,
            sleep_seconds=sleep_seconds,
        ),
    ):
        for table, count in ingest().items():
            totals[table] = totals.get(table, 0) + count
    return totals
