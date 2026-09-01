from basketball_api.ingestion import normalize_payload


def test_normalize_payload_builds_db_ready_rows() -> None:
    payload = {
        "teams": [
            {
                "id": 1610612760,
                "abbreviation": "OKC",
                "full_name": "Oklahoma City Thunder",
                "city": "Oklahoma City",
                "nickname": "Thunder",
            }
        ],
        "players": [
            {
                "id": 2544,
                "first_name": "Shai",
                "last_name": "Gilgeous-Alexander",
                "jersey_number": 2,
                "position": "G",
                "team_id": 1610612760,
            }
        ],
        "games": [
            {
                "id": 123,
                "season": "2024-25",
                "date": "2024-10-25",
                "status": "Final",
                "home_team_id": 1610612760,
                "away_team_id": 1610612747,
            }
        ],
        "team_games": [
            {"game_id": 123, "team_id": 1610612760, "is_home": True, "score": 120},
            {"game_id": 123, "team_id": 1610612747, "is_home": False, "score": 110},
        ],
        "shots": [
            {
                "event_number": 1,
                "made": True,
                "shot_type": "two",
                "distance": 18.4,
                "period": 1,
                "clock": "11:30",
                "x": 12.3,
                "y": 7.8,
                "game_id": 123,
                "team_id": 1610612760,
                "player_id": 2544,
            }
        ],
        "play_by_play": [
            {
                "event_number": 1,
                "event_type": "made_shot",
                "description": "SGA makes a jumper",
                "period": 1,
                "clock": "11:30",
                "score_text": "OKC 2 - 0 MIN",
                "game_id": 123,
                "team_id": 1610612760,
                "player_id": 2544,
            }
        ],
    }

    normalized = normalize_payload(payload)

    assert normalized["teams"][0]["nba_team_id"] == 1610612760
    assert normalized["players"][0]["nba_player_id"] == 2544
    assert normalized["games"][0]["nba_game_id"] == 123
    assert normalized["team_games"][0]["score"] == 120
    assert normalized["shots"][0]["shot_made"] is True
    assert normalized["play_by_play"][0]["event_type"] == "made_shot"
