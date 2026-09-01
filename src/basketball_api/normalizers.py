from __future__ import annotations

from typing import Any


def normalize_team(raw_team: dict[str, Any]) -> dict[str, Any]:
    """Normalize a single NBA team fixture into the canonical team fields."""
    return {
        "nba_team_id": int(raw_team["id"]),
        "abbreviation": str(raw_team["abbreviation"]),
        "full_name": str(raw_team["full_name"]),
        "city": str(raw_team["city"]),
        "nickname": str(raw_team["nickname"]),
    }


def normalize_player(raw_player: dict[str, Any], team_id: int) -> dict[str, Any]:
    """Normalize a single NBA player fixture into the canonical player fields."""
    return {
        "nba_player_id": int(raw_player["id"]),
        "team_id": team_id,
        "first_name": str(raw_player["first_name"]),
        "last_name": str(raw_player["last_name"]),
        "jersey_number": int(raw_player.get("jersey_number") or 0),
        "position": str(raw_player.get("position") or ""),
    }


def normalize_game(raw_game: dict[str, Any], home_team_id: int, away_team_id: int) -> dict[str, Any]:
    """Normalize a single NBA game fixture into the canonical game fields."""
    return {
        "nba_game_id": int(raw_game["id"]),
        "season": str(raw_game.get("season", "2024-25")),
        "game_date": str(raw_game["date"]),
        "home_team_id": home_team_id,
        "away_team_id": away_team_id,
        "status": str(raw_game.get("status", "scheduled")),
    }


def normalize_team_game(game_id: int, team_id: int, is_home: bool, score: int) -> dict[str, Any]:
    return {
        "game_id": game_id,
        "team_id": team_id,
        "is_home": is_home,
        "score": score,
    }


def normalize_shot(raw_shot: dict[str, Any], game_id: int, team_id: int, player_id: int) -> dict[str, Any]:
    return {
        "game_id": game_id,
        "team_id": team_id,
        "player_id": player_id,
        "event_number": int(raw_shot["event_number"]),
        "shot_made": bool(raw_shot.get("made", False)),
        "shot_type": str(raw_shot.get("shot_type") or ""),
        "shot_distance": float(raw_shot.get("distance") or 0.0),
        "period": int(raw_shot.get("period") or 1),
        "clock": str(raw_shot.get("clock") or ""),
        "x_coordinate": float(raw_shot.get("x") or 0.0),
        "y_coordinate": float(raw_shot.get("y") or 0.0),
    }


def normalize_play_by_play(raw_action: dict[str, Any], game_id: int, team_id: int | None, player_id: int | None) -> dict[str, Any]:
    return {
        "game_id": game_id,
        "team_id": team_id,
        "player_id": player_id,
        "event_number": int(raw_action["event_number"]),
        "event_type": str(raw_action.get("event_type") or raw_action.get("type") or ""),
        "description": str(raw_action.get("description") or ""),
        "period": int(raw_action.get("period") or 1),
        "clock": str(raw_action.get("clock") or ""),
        "score_text": str(raw_action.get("score_text") or ""),
    }
