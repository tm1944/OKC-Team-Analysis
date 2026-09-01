from basketball_api.normalizers import (
    normalize_game,
    normalize_play_by_play,
    normalize_player,
    normalize_shot,
    normalize_team,
    normalize_team_game,
)


def test_normalize_team() -> None:
    raw_team = {
        "id": 1610612760,
        "abbreviation": "OKC",
        "full_name": "Oklahoma City Thunder",
        "city": "Oklahoma City",
        "nickname": "Thunder",
    }

    normalized = normalize_team(raw_team)

    assert normalized["nba_team_id"] == 1610612760
    assert normalized["abbreviation"] == "OKC"
    assert normalized["full_name"] == "Oklahoma City Thunder"


def test_normalize_player() -> None:
    normalized = normalize_player({"id": 2544, "first_name": "Shai", "last_name": "Gilgeous-Alexander", "jersey_number": 2, "position": "G"}, 1)

    assert normalized["nba_player_id"] == 2544
    assert normalized["team_id"] == 1
    assert normalized["first_name"] == "Shai"
    assert normalized["position"] == "G"


def test_normalize_game() -> None:
    normalized = normalize_game({"id": 123, "date": "2024-10-25", "status": "Final"}, 1, 2)

    assert normalized["nba_game_id"] == 123
    assert normalized["home_team_id"] == 1
    assert normalized["away_team_id"] == 2
    assert normalized["status"] == "Final"


def test_normalize_team_game() -> None:
    normalized = normalize_team_game(10, 1, True, 120)

    assert normalized == {"game_id": 10, "team_id": 1, "is_home": True, "score": 120}


def test_normalize_shot() -> None:
    normalized = normalize_shot({"event_number": 5, "made": True, "shot_type": "two", "distance": 18.4, "period": 2, "clock": "04:20", "x": 12.3, "y": 7.8}, 10, 1, 2)

    assert normalized["event_number"] == 5
    assert normalized["shot_made"] is True
    assert normalized["team_id"] == 1
    assert normalized["period"] == 2


def test_normalize_play_by_play() -> None:
    normalized = normalize_play_by_play({"event_number": 7, "event_type": "made_shot", "description": "SGA makes a jumper", "period": 1, "clock": "01:30", "score_text": "OKC 8 - 6 MIN"}, 10, 1, 2)

    assert normalized["event_number"] == 7
    assert normalized["event_type"] == "made_shot"
    assert normalized["team_id"] == 1
    assert normalized["description"] == "SGA makes a jumper"
