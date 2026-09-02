#!/usr/bin/env python
"""Preview Oklahoma City shot data without touching PostgreSQL."""

from __future__ import annotations

import argparse
from typing import Any

from nba_api.stats.endpoints import shotchartdetail

from basketball_api.config import get_settings


def format_sample_shot(shot: Any) -> str:
    """Format one ShotChartDetail row for terminal output."""
    result = "made" if str(shot["EVENT_TYPE"]).casefold() == "made shot" else "missed"
    return (
        f"{shot['PLAYER_NAME']} | {result} | "
        f"{shot['SHOT_DISTANCE']} ft | {shot['SHOT_ZONE_BASIC']}"
    )


def preview_shots(season: str, team_id: int, team_abbreviation: str) -> int:
    """Fetch a team's season shot chart and print its first attempt."""
    response = shotchartdetail.ShotChartDetail(
        team_id=team_id,
        player_id=0,
        context_measure_simple="FGA",
        season_nullable=season,
        season_type_all_star="Regular Season",
    )
    shots = response.get_data_frames()[0]

    print(f"Season: {season}")
    print(f"{team_abbreviation.upper()} shots: {len(shots)}")

    if shots.empty:
        raise RuntimeError(f"No shots found for team ID {team_id}")

    print(f"Sample: {format_sample_shot(shots.iloc[0])}")
    return len(shots)


def parse_args() -> argparse.Namespace:
    settings = get_settings()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", default=settings.nba_season)
    parser.add_argument("--team-id", type=int, default=settings.nba_team_id)
    parser.add_argument("--team", default=settings.nba_team_abbreviation)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    preview_shots(args.season, args.team_id, args.team)


if __name__ == "__main__":
    main()

