from __future__ import annotations

import pandas as pd

from scripts.preview_league_games import select_team_games


def test_select_team_games_is_case_insensitive() -> None:
    frame = pd.DataFrame(
        {
            "TEAM_ABBREVIATION": ["BOS", "OKC", "OKC"],
            "GAME_ID": [1, 2, 3],
        }
    )

    selected = select_team_games(frame, "okc")

    assert selected["GAME_ID"].tolist() == [2, 3]

