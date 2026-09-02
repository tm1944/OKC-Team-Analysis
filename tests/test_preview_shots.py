from __future__ import annotations

import pandas as pd

from scripts.preview_shots import format_sample_shot


def test_format_sample_shot() -> None:
    shot = pd.Series(
        {
            "PLAYER_NAME": "Shai Gilgeous-Alexander",
            "EVENT_TYPE": "Made Shot",
            "SHOT_DISTANCE": 3,
            "SHOT_ZONE_BASIC": "Restricted Area",
        }
    )

    assert format_sample_shot(shot) == (
        "Shai Gilgeous-Alexander | made | 3 ft | Restricted Area"
    )

