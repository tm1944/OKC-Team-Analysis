"""Fetch and normalize the NBA source records needed for one team season."""

from __future__ import annotations

import json
import re
import time
from collections import defaultdict
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from nba_api.stats.endpoints import (
    commonteamroster,
    leaguegamelog,
    playbyplayv3,
    shotchartdetail,
)
from nba_api.stats.static import teams as static_teams

Record = dict[str, Any]


def _cache_path(cache_dir: Path, *parts: str) -> Path:
    return cache_dir.joinpath(*parts).with_suffix(".json")


def _read_or_fetch_records(
    cache_file: Path,
    fetch: Callable[[], list[Record]],
    *,
    refresh: bool,
) -> list[Record]:
    if cache_file.exists() and not refresh:
        return json.loads(cache_file.read_text(encoding="utf-8"))

    records = fetch()
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(records, indent=2, sort_keys=True), encoding="utf-8")
    return records


def _data_frame_records(response: Any) -> list[Record]:
    frame = response.get_data_frames()[0]
    return json.loads(frame.to_json(orient="records"))


def team_records(cache_dir: Path, *, refresh: bool) -> list[Record]:
    """Return static NBA team records in the shape expected by normalizers."""
    cache_file = _cache_path(cache_dir, "teams")
    return _read_or_fetch_records(
        cache_file,
        lambda: list(static_teams.get_teams()),
        refresh=refresh,
    )


def league_game_records(
    cache_dir: Path,
    *,
    season: str,
    team_id: int,
    refresh: bool,
) -> tuple[list[Record], list[Record]]:
    """Return game and team-game records for one team's regular-season schedule."""
    cache_file = _cache_path(cache_dir, season, "league_game_log")
    rows = _read_or_fetch_records(
        cache_file,
        lambda: _data_frame_records(
            leaguegamelog.LeagueGameLog(
                counter=0,
                direction="ASC",
                league_id="00",
                player_or_team_abbreviation="T",
                season=season,
                season_type_all_star="Regular Season",
                sorter="DATE",
            )
        ),
        refresh=refresh,
    )

    rows_by_game: dict[int, list[Record]] = defaultdict(list)
    for row in rows:
        rows_by_game[int(row["GAME_ID"])].append(row)

    games: list[Record] = []
    team_games: list[Record] = []
    for game_id, game_rows in rows_by_game.items():
        team_row = next(
            (row for row in game_rows if int(row["TEAM_ID"]) == team_id),
            None,
        )
        if team_row is None:
            continue

        opponent_row = next((row for row in game_rows if row is not team_row), None)
        if opponent_row is None:
            raise ValueError(f"NBA game {game_id} is missing its opponent team record")

        # The selected team's own MATCHUP is the source of truth.  This also
        # works for neutral-site games where the opponent row can be marked
        # with "@" as well.
        selected_team_is_home = " vs. " in str(team_row["MATCHUP"])
        home_row, away_row = (
            (team_row, opponent_row)
            if selected_team_is_home
            else (opponent_row, team_row)
        )

        games.append(
            {
                "id": game_id,
                "season": season,
                "date": home_row["GAME_DATE"],
                "home_team_id": int(home_row["TEAM_ID"]),
                "away_team_id": int(away_row["TEAM_ID"]),
                "status": "Final",
            }
        )
        for row, is_home in ((home_row, True), (away_row, False)):
            team_games.append(
                {
                    "game_id": game_id,
                    "team_id": int(row["TEAM_ID"]),
                    "is_home": is_home,
                    "score": int(row["PTS"]),
                }
            )

    return games, team_games


def _split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split()
    if len(parts) < 2:
        return full_name, ""
    return " ".join(parts[:-1]), parts[-1]


def roster_records(
    cache_dir: Path,
    *,
    season: str,
    team_id: int,
    refresh: bool,
) -> list[Record]:
    """Return one team's roster in the shape expected by normalizers."""
    cache_file = _cache_path(cache_dir, season, f"roster_{team_id}")

    def fetch_roster() -> list[Record]:
        return _data_frame_records(
            commonteamroster.CommonTeamRoster(team_id=team_id, season=season)
        )

    rows = _read_or_fetch_records(
        cache_file,
        fetch_roster,
        refresh=refresh,
    )
    players: list[Record] = []
    for row in rows:
        first_name, last_name = _split_name(str(row["PLAYER"]))
        players.append(
            {
                "id": int(row["PLAYER_ID"]),
                "team_id": int(row["TeamID"]),
                "first_name": first_name,
                "last_name": last_name,
                "jersey_number": row.get("NUM"),
                "position": row.get("POSITION"),
            }
        )
    return players


def shot_records(
    cache_dir: Path,
    *,
    season: str,
    team_id: int,
    refresh: bool,
) -> list[Record]:
    """Return one team's regular-season shot attempts in canonical raw fields."""
    cache_file = _cache_path(cache_dir, season, f"shots_{team_id}")
    rows = _read_or_fetch_records(
        cache_file,
        lambda: _data_frame_records(
            shotchartdetail.ShotChartDetail(
                team_id=team_id,
                player_id=0,
                context_measure_simple="FGA",
                season_nullable=season,
                season_type_all_star="Regular Season",
            )
        ),
        refresh=refresh,
    )
    return [
        {
            "game_id": int(row["GAME_ID"]),
            "team_id": int(row["TEAM_ID"]),
            "player_id": int(row["PLAYER_ID"]),
            "player_name": str(row["PLAYER_NAME"]),
            "event_number": int(row["GAME_EVENT_ID"]),
            "made": bool(row["SHOT_MADE_FLAG"]),
            "shot_type": row["SHOT_TYPE"],
            "distance": row["SHOT_DISTANCE"],
            "period": row["PERIOD"],
            "clock": f"{int(row['MINUTES_REMAINING']):02}:{int(row['SECONDS_REMAINING']):02}",
            "x": row["LOC_X"],
            "y": row["LOC_Y"],
        }
        for row in rows
    ]


def player_records_from_shots(shots: Iterable[Record]) -> list[Record]:
    """Return minimal player records for historical players found in shot data.

    CommonTeamRoster reflects a current roster, so it may omit a player who
    appeared for the team earlier in the requested season.
    """
    players: dict[int, Record] = {}
    for shot in shots:
        player_id = int(shot["player_id"])
        first_name, last_name = _split_name(str(shot["player_name"]))
        players[player_id] = {
            "id": player_id,
            "team_id": int(shot["team_id"]),
            "first_name": first_name,
            "last_name": last_name,
            "jersey_number": 0,
            "position": "",
        }
    return list(players.values())


def _clock_from_iso_duration(clock: str) -> str:
    match = re.fullmatch(r"PT(?:(\d+)M)?(\d+(?:\.\d+)?)S", clock)
    if match is None:
        return clock
    minutes = int(match.group(1) or 0)
    seconds = int(float(match.group(2)))
    return f"{minutes:02}:{seconds:02}"


def _play_by_play_records(rows: Iterable[Record]) -> tuple[list[Record], list[Record]]:
    players: dict[int, Record] = {}
    actions: list[Record] = []
    for row in rows:
        team_id = int(row["teamId"]) or None
        player_id = int(row["personId"]) or None
        player_name = str(row.get("playerName") or "").strip()
        if (
            team_id is None
            or not player_name
            or player_id == team_id
            or (player_id is not None and player_id >= 1_000_000_000)
        ):
            player_id = None
        if team_id is not None and player_id is not None and player_name:
            first_name, last_name = _split_name(player_name)
            players[player_id] = {
                "id": player_id,
                "team_id": team_id,
                "first_name": first_name,
                "last_name": last_name,
                "jersey_number": 0,
                "position": "",
            }

        score_home = str(row.get("scoreHome") or "0")
        score_away = str(row.get("scoreAway") or "0")
        action_type = str(row.get("actionType") or "")
        sub_type = str(row.get("subType") or "")
        actions.append(
            {
                "game_id": int(row["gameId"]),
                "team_id": team_id,
                "player_id": player_id,
                # actionNumber can repeat when the NBA corrects an event.
                # actionId is the stable unique identifier for the action.
                "event_number": int(row.get("actionId") or row["actionNumber"]),
                "event_type": ":".join(part for part in (action_type, sub_type) if part),
                "description": row.get("description"),
                "period": int(row["period"]),
                "clock": _clock_from_iso_duration(str(row["clock"])),
                "score_text": f"{score_home}-{score_away}",
            }
        )
    return list(players.values()), actions


def play_by_play_records(
    cache_dir: Path,
    *,
    season: str,
    game_ids: Iterable[int],
    refresh: bool,
    sleep_seconds: float,
) -> tuple[list[Record], list[Record]]:
    """Return player and action records for the supplied games, caching each game."""
    all_players: dict[int, Record] = {}
    all_actions: list[Record] = []
    for game_id in game_ids:
        cache_file = _cache_path(cache_dir, season, "play_by_play", str(game_id))
        rows = _read_or_fetch_records(
            cache_file,
            lambda game_id=game_id: _data_frame_records(
                playbyplayv3.PlayByPlayV3(game_id=f"{game_id:010d}")
            ),
            refresh=refresh,
        )
        players, actions = _play_by_play_records(rows)
        all_players.update({player["id"]: player for player in players})
        all_actions.extend(actions)
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
    return list(all_players.values()), all_actions
