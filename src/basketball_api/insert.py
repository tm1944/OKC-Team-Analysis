from __future__ import annotations

from typing import Any


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
            INSERT INTO players (nba_player_id, team_id, first_name, last_name, jersey_number, position)
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


def insert_normalized_payload(conn: Any, normalized: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    """
    Take normalized row dictionaries from normalize_payload() and insert them into the database.
    Returns a summary of rows inserted per table.
    """
    return {
        "teams": insert_teams(conn, normalized.get("teams", [])),
        "players": insert_players(conn, normalized.get("players", [])),
        "games": insert_games(conn, normalized.get("games", [])),
        "team_games": insert_team_games(conn, normalized.get("team_games", [])),
        "shots": insert_shots(conn, normalized.get("shots", [])),
        "play_by_play": insert_play_by_play(conn, normalized.get("play_by_play", [])),
    }
