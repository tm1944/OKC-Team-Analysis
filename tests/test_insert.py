from __future__ import annotations

from typing import Any

import pytest

from basketball_api.insert import insert_normalized_payload, insert_teams


class FakeConnection:
    """Fake connection for testing insert operations."""

    def __init__(self) -> None:
        self.executed_queries: list[tuple[str, tuple[Any, ...]]] = []

    def execute(self, query: str, params: tuple[Any, ...] = ()) -> None:
        self.executed_queries.append((query, params))


def test_insert_teams_upserts_on_nba_team_id() -> None:
    conn = FakeConnection()
    teams = [
        {
            "nba_team_id": 1610612760,
            "abbreviation": "OKC",
            "full_name": "Oklahoma City Thunder",
            "city": "Oklahoma City",
            "nickname": "Thunder",
        }
    ]

    count = insert_teams(conn, teams)

    assert count == 1
    assert len(conn.executed_queries) == 1
    query, params = conn.executed_queries[0]
    assert "ON CONFLICT (nba_team_id) DO UPDATE" in query
    assert params[0] == 1610612760


def test_insert_normalized_payload_returns_counts() -> None:
    conn = FakeConnection()
    normalized = {
        "teams": [
            {
                "nba_team_id": 1610612760,
                "abbreviation": "OKC",
                "full_name": "Oklahoma City Thunder",
                "city": "Oklahoma City",
                "nickname": "Thunder",
            }
        ],
        "players": [
            {
                "nba_player_id": 2544,
                "team_id": 1,
                "first_name": "Shai",
                "last_name": "Gilgeous-Alexander",
                "jersey_number": 2,
                "position": "G",
            }
        ],
        "games": [],
        "team_games": [],
        "shots": [],
        "play_by_play": [],
    }

    counts = insert_normalized_payload(conn, normalized)

    assert counts["teams"] == 1
    assert counts["players"] == 1
    assert counts["games"] == 0
    assert counts["team_games"] == 0
    assert counts["shots"] == 0
    assert counts["play_by_play"] == 0
