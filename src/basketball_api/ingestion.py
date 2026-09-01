from __future__ import annotations

from typing import Any

from basketball_api.normalizers import (
    normalize_game,
    normalize_play_by_play,
    normalize_player,
    normalize_shot,
    normalize_team,
    normalize_team_game,
)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _coerce_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    return int(value)


def normalize_payload(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Normalize an external NBA payload into canonical DB-ready row dictionaries."""
    teams = _as_list(payload.get("teams"))
    players = _as_list(payload.get("players"))
    games = _as_list(payload.get("games"))
    team_games = _as_list(payload.get("team_games"))
    shots = _as_list(payload.get("shots"))
    play_by_play = _as_list(payload.get("play_by_play") or payload.get("play_by_play_actions"))

    normalized: dict[str, list[dict[str, Any]]] = {
        "teams": [normalize_team(team) for team in teams],
        "players": [],
        "games": [],
        "team_games": [],
        "shots": [],
        "play_by_play": [],
    }

    for player in players:
        team_value = player.get("team_id")
        if team_value is None and isinstance(player.get("team"), dict):
            team_value = player["team"].get("id")
        normalized["players"].append(normalize_player(player, _coerce_int(team_value)))

    for game in games:
        home_value = game.get("home_team_id")
        away_value = game.get("away_team_id")
        if home_value is None and isinstance(game.get("home_team"), dict):
            home_value = game["home_team"].get("id")
        if away_value is None and isinstance(game.get("away_team"), dict):
            away_value = game["away_team"].get("id")
        normalized["games"].append(normalize_game(game, _coerce_int(home_value), _coerce_int(away_value)))

    for team_game in team_games:
        normalized["team_games"].append(
            normalize_team_game(
                _coerce_int(team_game.get("game_id")),
                _coerce_int(team_game.get("team_id")),
                bool(team_game.get("is_home", False)),
                _coerce_int(team_game.get("score", 0)),
            )
        )

    for shot in shots:
        normalized["shots"].append(
            normalize_shot(
                shot,
                _coerce_int(shot.get("game_id")),
                _coerce_int(shot.get("team_id")),
                _coerce_int(shot.get("player_id")),
            )
        )

    for action in play_by_play:
        normalized["play_by_play"].append(
            normalize_play_by_play(
                action,
                _coerce_int(action.get("game_id")),
                _coerce_int(action.get("team_id")) if action.get("team_id") is not None else None,
                _coerce_int(action.get("player_id")) if action.get("player_id") is not None else None,
            )
        )

    return normalized
