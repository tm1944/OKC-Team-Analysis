from __future__ import annotations

from basketball_api.nba_sources import (
    _clock_from_iso_duration,
    _play_by_play_records,
    league_game_records,
    player_records_from_shots,
)


def test_clock_from_iso_duration() -> None:
    assert _clock_from_iso_duration("PT12M00.00S") == "12:00"
    assert _clock_from_iso_duration("PT3M5.00S") == "03:05"


def test_play_by_play_records_builds_players_and_actions() -> None:
    players, actions = _play_by_play_records(
        [
            {
                "gameId": "0022400075",
                "actionId": 9012,
                "actionNumber": 12,
                "clock": "PT11M05.00S",
                "period": 1,
                "teamId": 1610612760,
                "personId": 1628983,
                "playerName": "Shai Gilgeous-Alexander",
                "scoreHome": "2",
                "scoreAway": "0",
                "description": "Shai Gilgeous-Alexander makes a layup",
                "actionType": "2pt",
                "subType": "Layup",
            }
        ]
    )

    assert players[0]["id"] == 1628983
    assert players[0]["first_name"] == "Shai"
    assert actions[0]["game_id"] == 22400075
    assert actions[0]["clock"] == "11:05"
    assert actions[0]["event_type"] == "2pt:Layup"
    assert actions[0]["event_number"] == 9012


def test_play_by_play_records_keeps_team_events_playerless() -> None:
    players, actions = _play_by_play_records(
        [
            {
                "gameId": "0022400075",
                "actionNumber": 3,
                "clock": "PT12M00.00S",
                "period": 1,
                "teamId": 1610612760,
                "personId": 1610612760,
                "description": "Team turnover",
            }
        ]
    )

    assert players == []
    assert actions[0]["player_id"] is None


def test_play_by_play_records_keeps_official_events_playerless() -> None:
    _, actions = _play_by_play_records(
        [
            {
                "gameId": "0022400075",
                "actionNumber": 450,
                "clock": "PT05M33.00S",
                "period": 3,
                "teamId": 0,
                "personId": 447,
                "description": "Instant Replay",
            }
        ]
    )

    assert actions[0]["player_id"] is None


def test_player_records_from_shots_includes_historical_player() -> None:
    players = player_records_from_shots(
        [
            {
                "player_id": 1642024,
                "team_id": 1610612760,
                "player_name": "Branden Carlson",
            }
        ]
    )

    assert players == [
        {
            "id": 1642024,
            "team_id": 1610612760,
            "first_name": "Branden",
            "last_name": "Carlson",
            "jersey_number": 0,
            "position": "",
        }
    ]


def test_league_game_records_selects_one_team_schedule(tmp_path, monkeypatch) -> None:
    rows = [
        {
            "GAME_ID": "0022400075",
            "TEAM_ID": 1610612760,
            "MATCHUP": "OKC @ DEN",
            "GAME_DATE": "2024-10-24",
            "PTS": 102,
        },
        {
            "GAME_ID": "0022400075",
            "TEAM_ID": 1610612743,
            "MATCHUP": "DEN vs. OKC",
            "GAME_DATE": "2024-10-24",
            "PTS": 87,
        },
    ]

    def return_rows(*_args, **_kwargs):
        return rows

    monkeypatch.setattr("basketball_api.nba_sources._read_or_fetch_records", return_rows)

    games, team_games = league_game_records(
        tmp_path,
        season="2024-25",
        team_id=1610612760,
        refresh=False,
    )

    assert games == [
        {
            "id": 22400075,
            "season": "2024-25",
            "date": "2024-10-24",
            "home_team_id": 1610612743,
            "away_team_id": 1610612760,
            "status": "Final",
        }
    ]
    assert {row["team_id"] for row in team_games} == {1610612760, 1610612743}


def test_league_game_records_uses_selected_team_for_neutral_site(tmp_path, monkeypatch) -> None:
    rows = [
        {
            "GAME_ID": "0022401230",
            "TEAM_ID": 1610612745,
            "MATCHUP": "HOU @ OKC",
            "GAME_DATE": "2024-12-14",
            "PTS": 96,
        },
        {
            "GAME_ID": "0022401230",
            "TEAM_ID": 1610612760,
            "MATCHUP": "OKC @ HOU",
            "GAME_DATE": "2024-12-14",
            "PTS": 111,
        },
    ]

    def return_rows(*_args, **_kwargs):
        return rows

    monkeypatch.setattr("basketball_api.nba_sources._read_or_fetch_records", return_rows)

    games, _ = league_game_records(
        tmp_path,
        season="2024-25",
        team_id=1610612760,
        refresh=False,
    )

    assert games[0]["home_team_id"] == 1610612745
    assert games[0]["away_team_id"] == 1610612760
