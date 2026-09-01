#!/usr/bin/env python
"""Preview one season of NBA team game logs without touching PostgreSQL."""

from __future__ import annotations

import argparse
from typing import Any

from nba_api.stats.endpoints import leaguegamelog

from basketball_api.config import get_settings


def select_team_games(frame: Any, team_abbreviation: str) -> Any:
    """Return rows for one team from a LeagueGameLog data frame."""
    if "TEAM_ABBREVIATION" not in frame.columns:
        raise ValueError("LeagueGameLog response has no TEAM_ABBREVIATION column")

    abbreviation = team_abbreviation.upper()
    return frame[frame["TEAM_ABBREVIATION"].str.upper() == abbreviation]


def preview_games(season: str, team_abbreviation: str) -> int:
    """Fetch a season's team game logs and print a small OKC preview."""
    response = leaguegamelog.LeagueGameLog(
        counter=0,
        direction="ASC",
        league_id="00",
        player_or_team_abbreviation="T",
        season=season,
        season_type_all_star="Regular Season",
        sorter="DATE",
    )
    frame = response.get_data_frames()[0]
    team_games = select_team_games(frame, team_abbreviation)

    print(f"Season: {season}")
    print(f"{team_abbreviation.upper()} games: {len(team_games)}")

    if team_games.empty:
        raise RuntimeError(f"No games found for team {team_abbreviation.upper()}")

    first_game = team_games.iloc[0]
    print(
        "First game: "
        f"{first_game['GAME_ID']} | "
        f"{first_game['GAME_DATE']} | "
        f"{first_game['MATCHUP']}"
    )
    return len(team_games)


def parse_args() -> argparse.Namespace:
    settings = get_settings()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", default=settings.nba_season)
    parser.add_argument("--team", default=settings.nba_team_abbreviation)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    preview_games(args.season, args.team)


if __name__ == "__main__":
    main()

