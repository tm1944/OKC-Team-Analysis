from datetime import date, timedelta

import pytest

from basketball_api.splits import chronological_game_split


def _rows_for_games(game_count: int) -> list[dict[str, object]]:
    first_date = date(2024, 10, 1)
    rows: list[dict[str, object]] = []
    for game_id in range(1, game_count + 1):
        game_date = first_date + timedelta(days=game_id)
        rows.extend(
            [
                {"game_id": game_id, "game_date": game_date, "shot_id": f"{game_id}-a"},
                {"game_id": game_id, "game_date": game_date, "shot_id": f"{game_id}-b"},
            ]
        )
    return rows


def test_chronological_game_split_orders_and_keeps_games_together() -> None:
    rows = list(reversed(_rows_for_games(20)))

    train, validation, test = chronological_game_split(rows)

    assert {row["game_id"] for row in train} == set(range(1, 15))
    assert {row["game_id"] for row in validation} == set(range(15, 18))
    assert {row["game_id"] for row in test} == set(range(18, 21))
    assert [row["game_id"] for row in train] == [
        game_id for game_id in range(1, 15) for _ in range(2)
    ]


def test_chronological_game_split_has_no_overlap_or_missing_rows() -> None:
    rows = _rows_for_games(10)

    train, validation, test = chronological_game_split(rows)
    split_ids = [
        {row["game_id"] for row in split}
        for split in (train, validation, test)
    ]

    assert split_ids[0].isdisjoint(split_ids[1])
    assert split_ids[0].isdisjoint(split_ids[2])
    assert split_ids[1].isdisjoint(split_ids[2])
    assert {row["shot_id"] for row in train + validation + test} == {
        row["shot_id"] for row in rows
    }


def test_chronological_game_split_requires_three_games() -> None:
    with pytest.raises(ValueError, match="At least three unique games"):
        chronological_game_split(_rows_for_games(2))


def test_chronological_game_split_requires_one_date_per_game() -> None:
    with pytest.raises(ValueError, match="inconsistent game_date"):
        chronological_game_split(
            [
                {"game_id": 1, "game_date": "2024-10-01"},
                {"game_id": 1, "game_date": "2024-10-02"},
                {"game_id": 2, "game_date": "2024-10-03"},
                {"game_id": 3, "game_date": "2024-10-04"},
            ]
        )
