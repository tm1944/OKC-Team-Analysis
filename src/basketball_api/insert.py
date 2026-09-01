from __future__ import annotations

from typing import Any


def _lookup_ids(
    conn: Any,
    *,
    table: str,
    external_column: str,
    external_ids: set[int],
) -> dict[int, int]:
    if not external_ids:
        return {}

    query_by_table = {
        ("teams", "nba_team_id"): "SELECT nba_team_id, id FROM teams WHERE nba_team_id = ANY(%s)",
        ("players", "nba_player_id"): (
            "SELECT nba_player_id, id FROM players WHERE nba_player_id = ANY(%s)"
        ),
        ("games", "nba_game_id"): "SELECT nba_game_id, id FROM games WHERE nba_game_id = ANY(%s)",
    }
    query = query_by_table[(table, external_column)]
    cursor = conn.execute(query, (list(external_ids),))
    return {external_id: internal_id for external_id, internal_id in cursor.fetchall()}


def _require_id(id_map: dict[int, int], external_id: int, entity: str) -> int:
    try:
        return id_map[external_id]
    except KeyError as error:
        raise ValueError(f"Missing {entity} with NBA ID {external_id}") from error


def _resolved_players(conn: Any, players: list[dict[str, Any]]) -> list[dict[str, Any]]:
    team_ids = _lookup_ids(
        conn,
        table="teams",
        external_column="nba_team_id",
        external_ids={player["team_id"] for player in players},
    )
    return [
        {**player, "team_id": _require_id(team_ids, player["team_id"], "team")}
        for player in players
    ]


def _resolved_games(conn: Any, games: list[dict[str, Any]]) -> list[dict[str, Any]]:
    external_team_ids = {
        team_id
        for game in games
        for team_id in (game["home_team_id"], game["away_team_id"])
    }
    team_ids = _lookup_ids(
        conn,
        table="teams",
        external_column="nba_team_id",
        external_ids=external_team_ids,
    )
    return [
        {
            **game,
            "home_team_id": _require_id(team_ids, game["home_team_id"], "team"),
            "away_team_id": _require_id(team_ids, game["away_team_id"], "team"),
        }
        for game in games
    ]


def _resolved_fact_rows(
    conn: Any,
    rows: list[dict[str, Any]],
    *,
    include_player: bool,
) -> list[dict[str, Any]]:
    game_ids = _lookup_ids(
        conn,
        table="games",
        external_column="nba_game_id",
        external_ids={row["game_id"] for row in rows},
    )
    team_ids = _lookup_ids(
        conn,
        table="teams",
        external_column="nba_team_id",
        external_ids={row["team_id"] for row in rows if row.get("team_id") is not None},
    )
    player_ids = _lookup_ids(
        conn,
        table="players",
        external_column="nba_player_id",
        external_ids={row["player_id"] for row in rows if row.get("player_id") is not None},
    ) if include_player else {}

    resolved_rows: list[dict[str, Any]] = []
    for row in rows:
        resolved = {**row, "game_id": _require_id(game_ids, row["game_id"], "game")}
        if row.get("team_id") is not None:
            resolved["team_id"] = _require_id(team_ids, row["team_id"], "team")
        if include_player and row.get("player_id") is not None:
            resolved["player_id"] = _require_id(player_ids, row["player_id"], "player")
        resolved_rows.append(resolved)

    return resolved_rows


def insert_teams(conn: Any, teams: list[dict[str, Any]]) -> int:
    """Insert or update teams. Return count inserted."""
    if not teams:
        return 0

    rows_inserted = 0
    for team in teams:
        conn.execute(
            """
            INSERT INTO teams (nba_team_id, abbreviation, full_name, city, nickname)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (nba_team_id) DO UPDATE
            SET abbreviation = EXCLUDED.abbreviation,
                full_name = EXCLUDED.full_name,
                city = EXCLUDED.city,
                nickname = EXCLUDED.nickname
            """,
            (
                team["nba_team_id"],
                team["abbreviation"],
                team["full_name"],
                team["city"],
                team["nickname"],
            ),
        )
        rows_inserted += 1

    return rows_inserted


def insert_players(conn: Any, players: list[dict[str, Any]]) -> int:
    """Insert or update players. Return count inserted."""
    if not players:
        return 0

    rows_inserted = 0
    for player in players:
        conn.execute(
            """
            INSERT INTO players (
                nba_player_id, team_id, first_name, last_name, jersey_number, position
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (nba_player_id) DO UPDATE
            SET team_id = EXCLUDED.team_id,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                jersey_number = EXCLUDED.jersey_number,
                position = EXCLUDED.position
            """,
            (
                player["nba_player_id"],
                player["team_id"],
                player["first_name"],
                player["last_name"],
                player["jersey_number"],
                player["position"],
            ),
        )
        rows_inserted += 1

    return rows_inserted


def insert_games(conn: Any, games: list[dict[str, Any]]) -> int:
    """Insert or update games. Return count inserted."""
    if not games:
        return 0

    rows_inserted = 0
    for game in games:
        conn.execute(
            """
            INSERT INTO games (nba_game_id, season, game_date, home_team_id, away_team_id, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (nba_game_id) DO UPDATE
            SET season = EXCLUDED.season,
                game_date = EXCLUDED.game_date,
                home_team_id = EXCLUDED.home_team_id,
                away_team_id = EXCLUDED.away_team_id,
                status = EXCLUDED.status
            """,
            (
                game["nba_game_id"],
                game["season"],
                game["game_date"],
                game["home_team_id"],
                game["away_team_id"],
                game["status"],
            ),
        )
        rows_inserted += 1

    return rows_inserted


def insert_team_games(conn: Any, team_games: list[dict[str, Any]]) -> int:
    """Insert or update team_games. Return count inserted."""
    if not team_games:
        return 0

    rows_inserted = 0
    for tg in team_games:
        conn.execute(
            """
            INSERT INTO team_games (game_id, team_id, is_home, score)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (game_id, team_id) DO UPDATE
            SET is_home = EXCLUDED.is_home,
                score = EXCLUDED.score
            """,
            (tg["game_id"], tg["team_id"], tg["is_home"], tg["score"]),
        )
        rows_inserted += 1

    return rows_inserted


def insert_shots(conn: Any, shots: list[dict[str, Any]]) -> int:
    """Insert or update shots. Return count inserted."""
    if not shots:
        return 0

    rows_inserted = 0
    for shot in shots:
        conn.execute(
            """
            INSERT INTO shots (
                game_id, team_id, player_id, event_number, shot_made, shot_type,
                shot_distance, period, clock, x_coordinate, y_coordinate
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (game_id, event_number) DO UPDATE
            SET team_id = EXCLUDED.team_id,
                player_id = EXCLUDED.player_id,
                shot_made = EXCLUDED.shot_made,
                shot_type = EXCLUDED.shot_type,
                shot_distance = EXCLUDED.shot_distance,
                period = EXCLUDED.period,
                clock = EXCLUDED.clock,
                x_coordinate = EXCLUDED.x_coordinate,
                y_coordinate = EXCLUDED.y_coordinate
            """,
            (
                shot["game_id"],
                shot["team_id"],
                shot["player_id"],
                shot["event_number"],
                shot["shot_made"],
                shot["shot_type"],
                shot["shot_distance"],
                shot["period"],
                shot["clock"],
                shot["x_coordinate"],
                shot["y_coordinate"],
            ),
        )
        rows_inserted += 1

    return rows_inserted


def insert_play_by_play(conn: Any, actions: list[dict[str, Any]]) -> int:
    """Insert or update play_by_play_actions. Return count inserted."""
    if not actions:
        return 0

    rows_inserted = 0
    for action in actions:
        conn.execute(
            """
            INSERT INTO play_by_play_actions (
                game_id, team_id, player_id, event_number, event_type,
                description, period, clock, score_text
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (game_id, event_number) DO UPDATE
            SET team_id = EXCLUDED.team_id,
                player_id = EXCLUDED.player_id,
                event_type = EXCLUDED.event_type,
                description = EXCLUDED.description,
                period = EXCLUDED.period,
                clock = EXCLUDED.clock,
                score_text = EXCLUDED.score_text
            """,
            (
                action["game_id"],
                action["team_id"],
                action["player_id"],
                action["event_number"],
                action["event_type"],
                action["description"],
                action["period"],
                action["clock"],
                action["score_text"],
            ),
        )
        rows_inserted += 1

    return rows_inserted


def insert_normalized_payload(
    conn: Any, normalized: dict[str, list[dict[str, Any]]]
) -> dict[str, int]:
    """
    Take normalized row dictionaries from normalize_payload() and insert them into the database.
    Returns a summary of rows inserted per table.
    """
    teams = normalized.get("teams", [])
    players = normalized.get("players", [])
    games = normalized.get("games", [])
    team_games = normalized.get("team_games", [])
    shots = normalized.get("shots", [])
    play_by_play = normalized.get("play_by_play", [])

    counts = {"teams": insert_teams(conn, teams)}
    counts["players"] = insert_players(conn, _resolved_players(conn, players))
    counts["games"] = insert_games(conn, _resolved_games(conn, games))
    counts["team_games"] = insert_team_games(
        conn,
        _resolved_fact_rows(conn, team_games, include_player=False),
    )
    counts["shots"] = insert_shots(conn, _resolved_fact_rows(conn, shots, include_player=True))
    counts["play_by_play"] = insert_play_by_play(
        conn,
        _resolved_fact_rows(conn, play_by_play, include_player=True),
    )
    return counts
