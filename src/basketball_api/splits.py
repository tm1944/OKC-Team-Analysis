"""Chronological, whole-game dataset splits for model evaluation."""

from collections import defaultdict
from collections.abc import Iterable
from typing import Any

Split = tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]


def chronological_game_split(rows: Iterable[dict[str, Any]]) -> Split:
    """Split shot rows into chronological train, validation, and test groups.

    A game is the smallest unit that may be assigned to a split. This prevents
    shots from the same game appearing in both training and evaluation data.
    """
    rows_by_game: dict[int, list[dict[str, Any]]] = defaultdict(list)
    game_dates: dict[int, str] = {}

    for row in rows:
        game_id = int(row["game_id"])
        game_date = str(row["game_date"])
        previous_date = game_dates.setdefault(game_id, game_date)
        if previous_date != game_date:
            raise ValueError(f"Game {game_id} has inconsistent game_date values")
        rows_by_game[game_id].append(row)

    ordered_game_ids = sorted(rows_by_game, key=lambda game_id: (game_dates[game_id], game_id))
    game_count = len(ordered_game_ids)
    if game_count < 3:
        raise ValueError(
            "At least three unique games are required for train/validation/test splits"
        )

    train_count = int(game_count * 0.70)
    validation_count = int(game_count * 0.15)
    test_count = game_count - train_count - validation_count

    # Keep all three splits nonempty for small but valid datasets.
    if validation_count == 0:
        validation_count = 1
        train_count -= 1
    if test_count == 0:
        test_count = 1
        train_count -= 1

    train_ids = ordered_game_ids[:train_count]
    validation_ids = ordered_game_ids[train_count : train_count + validation_count]
    test_ids = ordered_game_ids[train_count + validation_count :]

    return (
        [row for game_id in train_ids for row in rows_by_game[game_id]],
        [row for game_id in validation_ids for row in rows_by_game[game_id]],
        [row for game_id in test_ids for row in rows_by_game[game_id]],
    )
